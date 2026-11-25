import hashlib
import re
from typing import ClassVar
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from app.core.logging import logger
from app.models.enums import WorkModelEnum
from app.models.job import JobItem
from app.providers.base import JobProviderStrategy, ProviderContext
from app.providers.registry import ProviderRegistry

CIANDT_OPORTUNIDADES_URL = "https://ciandt.com/br/pt-br/carreiras/oportunidades"
CIANDT_BASE_URL = "https://ciandt.com"
HEADERS_CIANDT = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def extrair_vagas_ciandt_html(
    conteudo_html: str,
    termos_interesse: list[str],
    apenas_remoto: bool,
    senioridade_filtro: str,
) -> list[JobItem]:
    sopa = BeautifulSoup(conteudo_html, "html.parser")
    cards = sopa.find_all("div", class_="opprtunity-item")
    vagas: list[JobItem] = []

    for card in cards:
        if not isinstance(card, Tag):
            continue

        h2_titulo = card.find("h2")
        link_tag = card.find("a", href=True)
        if not h2_titulo or not link_tag:
            continue

        titulo = h2_titulo.get_text(" ", strip=True)
        if not titulo:
            continue

        titulo_minusculo = titulo.lower()
        if termos_interesse and not any(termo in titulo_minusculo for termo in termos_interesse):
            continue

        filtros_span = card.find("span", class_="filters-item")
        texto_filtros = filtros_span.get_text(" ", strip=True) if filtros_span else ""
        texto_filtros_lower = texto_filtros.lower()

        local_div = card.find("div", class_="wp-block-cit-block-ciandt-short-text")
        localizacao_bruta = local_div.get_text(" ", strip=True) if local_div else "Brasil"
        localizacao = re.sub(r"\s+", " ", localizacao_bruta).strip() or "Brasil"

        eh_remoto = "workplace_type_remote" in texto_filtros_lower or "homeoffice" in texto_filtros_lower or "remoto" in titulo_minusculo
        modelo_trabalho = WorkModelEnum.REMOTO if eh_remoto else WorkModelEnum.HIBRIDO
        if apenas_remoto and modelo_trabalho != WorkModelEnum.REMOTO:
            continue

        href = str(link_tag["href"]).strip()
        link_completo = urljoin(CIANDT_BASE_URL, href)
        match_uuid = re.search(r"opportunity=([a-zA-Z0-9-]+)", href)
        url_hash = hashlib.sha256(link_completo.encode("utf-8")).hexdigest()[:16]
        job_id = f"ciandt_{match_uuid.group(1)}" if match_uuid else f"ciandt_{url_hash}"

        vagas.append(
            JobItem(
                job_id=job_id,
                provider="CI&T",
                titulo=titulo,
                empresa="CI&T",
                localizacao=localizacao,
                data_postagem="Recente",
                modelo_trabalho=modelo_trabalho,
                link=link_completo,
                descricao_resumida=f"CI&T - {titulo} ({localizacao})",
                descricao_completa=f"Vaga CI&T: {titulo}. Localização: {localizacao}. Filtros: {texto_filtros}",
            )
        )

    return vagas


@ProviderRegistry.register
class CiandtProvider(JobProviderStrategy):
    provider_name: ClassVar[str] = "CI&T"
    badge_colors: ClassVar[tuple[str, str]] = ("#e11d48", "#ffffff")
    supports_enrichment: ClassVar[bool] = False

    def search_jobs(self, context: ProviderContext) -> list[JobItem]:
        logger.info("🔴 [CI&T] Consultando portal de carreiras da CI&T...")
        termos_interesse = [termo.strip().lower() for termo in context.profile.termos_cargo_inhire if termo.strip()]

        try:
            resposta = requests.get(
                CIANDT_OPORTUNIDADES_URL,
                headers=HEADERS_CIANDT,
                timeout=max(context.settings.http_timeout, 10),
            )
            if resposta.status_code != 200:
                logger.warning(f"⚠️ [CI&T] Falha ao consultar portal CI&T: Status {resposta.status_code}")
                return []

            vagas = extrair_vagas_ciandt_html(
                conteudo_html=resposta.text,
                termos_interesse=termos_interesse,
                apenas_remoto=context.settings.apenas_remoto,
                senioridade_filtro=context.settings.senioridade_filtro,
            )
            logger.info(f"🔴 [CI&T] {len(vagas)} vagas pré-selecionadas extraídas.")
        except Exception as erro:
            logger.warning(f"⚠️ [CI&T] Erro ao buscar vagas na CI&T: {erro}")
            return []
        else:
            return vagas
