import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from tqdm import tqdm

from app.core.config import settings
from app.core.logging import logger

URL_API_INHIRE = "https://api.inhire.app/job-posts/public/pages"
HEADERS_VALIDACAO = {
    "User-Agent": "Mozilla/5.0",
    "X-Inhire-Client": "web-inhire",
    "Accept": "application/json",
}
SUBDOMINIOS_INFRA = {
    "api",
    "files",
    "staging",
    "app",
    "dev",
    "mail",
    "admin",
    "cdn",
    "auth",
    "login",
    "assets",
    "support",
    "docs",
}


def extrair_slugs_de_texto(texto: str) -> set[str]:
    padrao = re.compile(r"https?://([a-zA-Z0-9-]+)\.inhire\.app", re.IGNORECASE)
    slugs_encontrados: set[str] = set()
    for correspondencia in padrao.finditer(texto):
        slug = correspondencia.group(1).lower().strip()
        if len(slug) >= 2 and slug not in SUBDOMINIOS_INFRA:
            slugs_encontrados.add(slug)
    return slugs_encontrados


def colher_slugs_wayback(timeout: int = 20) -> set[str]:
    logger.info("🌐 [HARVESTER] Consultando Wayback Machine CDX para *.inhire.app...")
    url = "http://web.archive.org/cdx/search/cdx?url=*.inhire.app&output=text&fl=original&collapse=urlkey&limit=50000"
    try:
        resposta = requests.get(url, timeout=timeout)
        if resposta.status_code == 200:
            slugs = extrair_slugs_de_texto(resposta.text)
            logger.info(f"🌐 [HARVESTER] Wayback retornou {len(slugs)} slugs candidatos únicos.")
            return slugs
    except Exception as erro:
        logger.warning(f"⚠️ [HARVESTER] Falha na consulta do Wayback Machine: {erro}")
    return set()


def colher_slugs_urlscan(timeout: int = 15) -> set[str]:
    logger.info("🌐 [HARVESTER] Consultando urlscan.io para domain:inhire.app...")
    url = "https://urlscan.io/api/v1/search/?q=domain:inhire.app&size=100"
    slugs: set[str] = set()
    try:
        resposta = requests.get(url, timeout=timeout)
        if resposta.status_code == 200:
            dados = resposta.json()
            for resultado in dados.get("results", []):
                pagina_url = resultado.get("page", {}).get("url", "")
                slugs.update(extrair_slugs_de_texto(pagina_url))
            logger.info(f"🌐 [HARVESTER] urlscan.io retornou {len(slugs)} slugs candidatos.")
    except Exception as erro:
        logger.warning(f"⚠️ [HARVESTER] Falha na consulta do urlscan.io: {erro}")
    return slugs


def _validar_slug_tenant(slug: str, timeout: int) -> dict[str, str | int] | None:
    headers = {**HEADERS_VALIDACAO, "X-Tenant": slug}
    try:
        resposta = requests.get(URL_API_INHIRE, headers=headers, timeout=timeout)
        if resposta.status_code != 200:
            return None
        dados = resposta.json()
        if isinstance(dados, dict) and "tenantName" in dados:
            tenant_nome = dados.get("tenantName") or slug
            jobs_count = len(dados.get("jobsPage", []))
            return {
                "slug": slug,
                "tenantName": tenant_nome.strip(),
                "jobsCount": jobs_count,
            }
    except Exception:
        pass
    return None


def colher_e_validar_novos_tenants(
    caminho_arquivo_tenants: Path | None = None,
    max_workers: int = 15,
    timeout: int = 8,
) -> list[dict[str, str | int]]:
    arquivo_destino = caminho_arquivo_tenants or settings.inhire_tenants_file
    slugs_existentes: set[str] = set()
    tenants_existentes: list[dict[str, str | int]] = []

    if arquivo_destino.exists():
        try:
            with open(arquivo_destino, encoding="utf-8") as arquivo:
                tenants_existentes = json.load(arquivo)
                slugs_existentes = {str(item["slug"]).lower() for item in tenants_existentes if "slug" in item}
        except Exception:
            pass

    logger.info(f"📁 [HARVESTER] Tenants já conhecidos no arquivo: {len(slugs_existentes)}")

    slugs_candidatos = colher_slugs_wayback() | colher_slugs_urlscan()
    novos_candidatos = [slug for slug in slugs_candidatos if slug not in slugs_existentes]

    logger.info(f"🔎 [HARVESTER] Novos candidatos para validação na API InHire: {len(novos_candidatos)}")
    if not novos_candidatos:
        logger.info("✨ [HARVESTER] Nenhum novo tenant para validar.")
        return tenants_existentes

    novos_confirmados: list[dict[str, str | int]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futuros = {executor.submit(_validar_slug_tenant, slug=slug, timeout=timeout): slug for slug in novos_candidatos}
        with tqdm(total=len(novos_candidatos), desc="🔎 [HARVESTER] Validando Tenants", unit="slug") as barra:
            for futuro in as_completed(futuros):
                try:
                    resultado = futuro.result()
                    if resultado:
                        novos_confirmados.append(resultado)
                except Exception:
                    pass
                finally:
                    barra.update(1)

    logger.info(f"🎉 [HARVESTER] {len(novos_confirmados)} novos tenants reais confirmados!")
    todos_tenants = tenants_existentes + novos_confirmados
    # Deduplicar por slug
    tenants_dedup: dict[str, dict[str, str | int]] = {}
    for t in todos_tenants:
        slug_chave = str(t["slug"]).lower()
        tenants_dedup[slug_chave] = t

    lista_ordenada = sorted(tenants_dedup.values(), key=lambda item: str(item.get("tenantName", "")).lower())

    arquivo_destino.parent.mkdir(parents=True, exist_ok=True)
    with open(arquivo_destino, "w", encoding="utf-8") as arquivo:
        json.dump(lista_ordenada, arquivo, indent=2, ensure_ascii=False)

    logger.info(f"💾 [HARVESTER] Total de {len(lista_ordenada)} tenants salvos em '{arquivo_destino}'.")
    return lista_ordenada


if __name__ == "__main__":
    colher_e_validar_novos_tenants()
