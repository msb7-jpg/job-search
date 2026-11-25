import json
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import requests
from tqdm import tqdm

from app.core.logging import logger
from app.models.enums import TimeFilterEnum, WorkModelEnum
from app.models.job import JobItem
from app.shared.classifiers import avaliar_pre_filtro_job_bruto
from app.shared.html_formatter import html_to_markdown

INHIRE_PUBLIC_PAGES_URL = "https://api.inhire.app/job-posts/public/pages"
HEADERS_INHIRE_BASE = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
    "X-Inhire-Client": "web-inhire",
    "Accept": "application/json",
}


def slugificar_titulo(texto: str) -> str:
    texto_normalizado = unicodedata.normalize("NFD", texto)
    texto_sem_acentos = "".join(caractere for caractere in texto_normalizado if unicodedata.category(caractere) != "Mn")
    texto_limpo = re.sub(r"[^a-zA-Z0-9]+", "-", texto_sem_acentos.lower()).strip("-")
    return texto_limpo or "vaga"


def _limpar_html_descricao(texto_html: str | None) -> str:
    return html_to_markdown(texto_html or "")


def _verificar_recencia(
    data_iso: str | None,
    filtro_tempo: TimeFilterEnum,
) -> bool:
    dias_limite = filtro_tempo.dias_maximos
    if dias_limite is None or not data_iso:
        return True

    try:
        data_limpa = data_iso.replace("Z", "+00:00")
        data_publicacao = datetime.fromisoformat(data_limpa)
        agora = datetime.now(UTC)
        dias_diferenca = (agora - data_publicacao).total_seconds() / 86400.0
    except Exception:
        return True
    else:
        return dias_diferenca <= dias_limite


def _formatar_data_postagem(data_iso: str | None) -> str:
    if not data_iso:
        return "Recente"
    try:
        data_limpa = data_iso.replace("Z", "+00:00")
        data_obj = datetime.fromisoformat(data_limpa)
        return data_obj.strftime("%d/%m/%Y")
    except Exception:
        return data_iso[:10] if len(data_iso) >= 10 else "Recente"


def carregar_tenants_inhire(caminho_arquivo: Path) -> list[dict[str, str]]:
    if not caminho_arquivo.exists():
        logger.warning(f"⚠️ [INHIRE] Arquivo de tenants '{caminho_arquivo}' não encontrado.")
        return []

    try:
        with open(caminho_arquivo, encoding="utf-8") as arquivo:
            conteudo = json.load(arquivo)
        tenants: list[dict[str, str]] = []
        for item in conteudo:
            slug = item.get("slug")
            tenant_nome = item.get("tenantName") or slug
            if slug:
                tenants.append({"slug": str(slug).strip(), "tenantName": str(tenant_nome).strip()})
    except Exception as erro:
        logger.error(f"❌ [INHIRE] Erro ao carregar tenants de '{caminho_arquivo}': {erro}")
        return []
    else:
        return tenants


def _avaliar_vaga_tenant(
    vaga: dict,
    slug: str,
    tenant_nome: str,
    termos_cargo_inhire: list[str],
    apenas_remoto: bool,
    senioridade_filtro: str,
) -> dict[str, str] | None:
    status_vaga = str(vaga.get("status") or "").lower()
    if status_vaga and status_vaga != "published":
        return None

    titulo_vaga = (vaga.get("displayName") or "").strip()
    if not titulo_vaga:
        return None

    titulo_minusculo = titulo_vaga.lower()
    if not any(termo in titulo_minusculo for termo in termos_cargo_inhire):
        return None

    localizacao = vaga.get("location") or "Brasil"
    aprovado_pre, _motivo = avaliar_pre_filtro_job_bruto(
        titulo=titulo_vaga,
        localizacao=localizacao,
        apenas_remoto=apenas_remoto,
        senioridade_filtro=senioridade_filtro,
        empresa=tenant_nome,
    )
    if not aprovado_pre:
        return None

    modalidade_str = str(vaga.get("workplaceType") or "").lower()
    if "remote" in modalidade_str or "remoto" in modalidade_str:
        modelo_trabalho = WorkModelEnum.REMOTO
    elif "hybrid" in modalidade_str or "hibrido" in modalidade_str:
        modelo_trabalho = WorkModelEnum.HIBRIDO
    else:
        modelo_trabalho = WorkModelEnum.PRESENCIAL

    if apenas_remoto and modelo_trabalho != WorkModelEnum.REMOTO:
        return None

    job_id = str(vaga.get("jobId") or "")
    if not job_id:
        return None

    slug_titulo = slugificar_titulo(titulo_vaga)
    url_vaga = f"https://{slug}.inhire.app/vagas/{job_id}/{slug_titulo}"

    return {
        "job_id": job_id,
        "slug": slug,
        "empresa": tenant_nome,
        "titulo": titulo_vaga,
        "localizacao": localizacao,
        "modelo_trabalho": modelo_trabalho.value,
        "url": url_vaga,
    }


def _consultar_tenant_inhire(
    tenant_info: dict[str, str],
    termos_cargo_inhire: list[str],
    apenas_remoto: bool,
    senioridade_filtro: str,
    timeout: int,
) -> list[dict[str, str]]:
    slug = tenant_info["slug"]
    tenant_nome = tenant_info["tenantName"]
    headers = {**HEADERS_INHIRE_BASE, "X-Tenant": slug}

    try:
        resposta = requests.get(INHIRE_PUBLIC_PAGES_URL, headers=headers, timeout=timeout)
        if resposta.status_code != 200:
            return []

        dados = resposta.json()
        if not isinstance(dados, dict):
            return []

        paginas_vagas = dados.get("jobsPage", [])
        if not isinstance(paginas_vagas, list):
            return []

        vagas_aprovadas: list[dict[str, str]] = []
        for vaga in paginas_vagas:
            item_aprovado = _avaliar_vaga_tenant(
                vaga=vaga,
                slug=slug,
                tenant_nome=tenant_nome,
                termos_cargo_inhire=termos_cargo_inhire,
                apenas_remoto=apenas_remoto,
                senioridade_filtro=senioridade_filtro,
            )
            if item_aprovado:
                vagas_aprovadas.append(item_aprovado)
    except Exception:
        return []
    else:
        return vagas_aprovadas


def enriquecer_vaga_inhire(
    vaga: JobItem,
    filtro_tempo: TimeFilterEnum,
    timeout: int,
) -> JobItem | None:
    hostname = urlparse(vaga.link).hostname or ""
    slug = hostname.removesuffix(".inhire.app")
    job_id = vaga.job_id.removeprefix("inhire_")
    if not slug or not job_id:
        return vaga

    headers = {**HEADERS_INHIRE_BASE, "X-Tenant": slug}
    url_detalhe = f"{INHIRE_PUBLIC_PAGES_URL}/{job_id}"

    try:
        resposta = requests.get(url_detalhe, headers=headers, timeout=timeout)
        if resposta.status_code == 200:
            dados = resposta.json()
            if isinstance(dados, dict):
                data_publicacao_iso = dados.get("publishedAt") or dados.get("createdAt")
                if not _verificar_recencia(data_publicacao_iso, filtro_tempo):
                    return None
                vaga.data_postagem = _formatar_data_postagem(data_publicacao_iso)
                descricao_bruta = dados.get("description") or dados.get("about") or ""
                descricao_limpa = _limpar_html_descricao(descricao_bruta)
                vaga.descricao_completa = descricao_limpa
                vaga.descricao_resumida = descricao_limpa[:300]
    except Exception:
        pass

    return vaga


def buscar_vagas_candidatas_inhire(
    caminho_tenants: Path,
    termos_cargo_inhire: list[str],
    apenas_remoto: bool,
    senioridade_filtro: str,
    max_workers: int,
    timeout: int,
) -> list[JobItem]:
    tenants = carregar_tenants_inhire(caminho_tenants)
    if not tenants:
        return []

    logger.info(f"🟢 [INHIRE] Iniciando varredura concorrente em {len(tenants)} empresas (tenants)...")

    vagas_candidatas: list[dict[str, str]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futuros = {
            executor.submit(
                _consultar_tenant_inhire,
                tenant_info=tenant,
                termos_cargo_inhire=termos_cargo_inhire,
                apenas_remoto=apenas_remoto,
                senioridade_filtro=senioridade_filtro,
                timeout=timeout,
            ): tenant
            for tenant in tenants
        }
        with tqdm(total=len(tenants), desc="🟢 [INHIRE] Varrendo Tenants", unit="empresa") as barra_progresso:
            for futuro in as_completed(futuros):
                try:
                    resultado = futuro.result()
                    if resultado:
                        vagas_candidatas.extend(resultado)
                except Exception:
                    pass
                finally:
                    barra_progresso.update(1)

    logger.info(f"🟢 [INHIRE] Varredura concluída: {len(vagas_candidatas)} vagas pré-selecionadas.")

    vagas_finais: list[JobItem] = []
    for vaga in vagas_candidatas:
        modelo = WorkModelEnum.REMOTO if vaga["modelo_trabalho"] == WorkModelEnum.REMOTO.value else WorkModelEnum.PRESENCIAL
        vagas_finais.append(
            JobItem(
                job_id=f"inhire_{vaga['job_id']}",
                provider="InHire",
                titulo=vaga["titulo"],
                empresa=vaga["empresa"],
                localizacao=vaga["localizacao"],
                data_postagem="Recente",
                modelo_trabalho=modelo,
                link=vaga["url"],
                descricao_resumida="",
                descricao_completa="",
            )
        )
    return vagas_finais
