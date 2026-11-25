from typing import ClassVar

import requests

from app.core.logging import logger
from app.models.enums import SeniorityEnum, WorkModelEnum
from app.models.job import JobItem
from app.providers.base import JobProviderStrategy, ProviderContext
from app.providers.registry import ProviderRegistry
from app.shared.html_formatter import html_to_markdown

FULLSTACK_PUBLIC_API_URL = "https://api-v1.fullstack.com/api/job-postings/public"
FULLSTACK_DETAIL_API_URL = "https://api-v1.fullstack.com/api/job-postings"
FULLSTACK_PORTAL_JOB_URL = "https://talent.fullstack.com/jobs"
HEADERS_FULLSTACK = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


def _limpar_html(texto_html: str) -> str:
    return html_to_markdown(texto_html)


def _mapear_modelo_trabalho_fullstack(workplace_type: str | None) -> WorkModelEnum:
    texto = (workplace_type or "").strip().lower()
    if "remote" in texto:
        return WorkModelEnum.REMOTO
    if "hybrid" in texto:
        return WorkModelEnum.HIBRIDO
    if "on-site" in texto or "onsite" in texto:
        return WorkModelEnum.PRESENCIAL
    return WorkModelEnum.NAO_ESPECIFICADO


def _mapear_senioridade_fullstack(seniority_str: str | None) -> SeniorityEnum:
    texto = (seniority_str or "").strip().lower()
    if any(termo in texto for termo in ["entry", "junior", "associate", "intern"]):
        return SeniorityEnum.JUNIOR
    if "mid" in texto:
        return SeniorityEnum.PLENO
    if any(termo in texto for termo in ["senior", "lead", "staff", "principal", "director"]):
        return SeniorityEnum.SENIOR
    return SeniorityEnum.NAO_ESPECIFICADO


def converter_item_fullstack(
    item: dict,
    termos_interesse: list[str],
    apenas_remoto: bool,
    senioridade_filtro: str,
) -> JobItem | None:
    if not item.get("isPublished", True):
        return None

    posting_id = str(item.get("id") or "").strip()
    titulo = str(item.get("jobTitle") or "").strip()
    if not posting_id or not titulo:
        return None

    skills_names = [str(skill).strip() for skill in (item.get("skillsNames") or []) if skill]
    texto_combinado = f"{titulo} {' '.join(skills_names)}".lower()
    if termos_interesse and not any(termo in texto_combinado for termo in termos_interesse):
        return None

    modelo_trabalho = _mapear_modelo_trabalho_fullstack(item.get("linkedInWorkplaceType"))
    if apenas_remoto and modelo_trabalho != WorkModelEnum.REMOTO:
        return None

    senioridade = _mapear_senioridade_fullstack(item.get("linkedInSeniority"))
    if senioridade_filtro == "JUNIOR" and senioridade in (SeniorityEnum.PLENO, SeniorityEnum.SENIOR):
        return None

    partes_local = [str(part).strip() for part in [item.get("city"), item.get("state"), item.get("region")] if part]
    localizacao = ", ".join(partes_local) if partes_local else "Remote"

    descricao_inicial = f"Skills: {', '.join(skills_names)}" if skills_names else titulo
    link = f"{FULLSTACK_PORTAL_JOB_URL}?jobId={posting_id}"

    return JobItem(
        job_id=f"fullstack_{posting_id}",
        provider="FullStack",
        titulo=titulo,
        empresa="FullStack",
        localizacao=localizacao,
        data_postagem="Recente",
        senioridade=senioridade,
        modelo_trabalho=modelo_trabalho,
        link=link,
        descricao_resumida=descricao_inicial[:300],
        descricao_completa=descricao_inicial,
    )


@ProviderRegistry.register
class FullStackProvider(JobProviderStrategy):
    provider_name: ClassVar[str] = "FullStack"
    badge_colors: ClassVar[tuple[str, str]] = ("#0284c7", "#ffffff")
    supports_enrichment: ClassVar[bool] = True

    def enrichment_workers(self, context: ProviderContext) -> int:
        return 8

    def search_jobs(self, context: ProviderContext) -> list[JobItem]:
        logger.info("🔵 [FULLSTACK] Consultando API pública do FullStack Connect...")
        termos_interesse = [termo.strip().lower() for termo in context.profile.termos_cargo_inhire if termo.strip()]
        vagas_candidatas: list[JobItem] = []
        max_paginas = 3
        timeout = max(context.settings.http_timeout, 8)

        for pagina in range(1, max_paginas + 1):
            try:
                resposta = requests.get(
                    FULLSTACK_PUBLIC_API_URL,
                    params={"page": pagina, "take": 30},
                    headers=HEADERS_FULLSTACK,
                    timeout=timeout,
                )
                if resposta.status_code != 200:
                    break

                payload = resposta.json()
                itens = payload.get("data") or []
                if not itens:
                    break

                for item in itens:
                    vaga = converter_item_fullstack(
                        item=item,
                        termos_interesse=termos_interesse,
                        apenas_remoto=context.settings.apenas_remoto,
                        senioridade_filtro=context.settings.senioridade_filtro,
                    )
                    if vaga:
                        vagas_candidatas.append(vaga)

                if len(itens) < 30:
                    break
            except Exception as erro:
                logger.warning(f"⚠️ [FULLSTACK] Erro na página {pagina}: {erro}")
                break

        return vagas_candidatas

    def enrich_job(self, job: JobItem, context: ProviderContext) -> JobItem | None:
        posting_id = job.job_id.removeprefix("fullstack_")
        url_detalhe = f"{FULLSTACK_DETAIL_API_URL}/{posting_id}"
        timeout = max(context.settings.http_timeout, 8)
        try:
            resposta = requests.get(url_detalhe, headers=HEADERS_FULLSTACK, timeout=timeout)
            if resposta.status_code == 200:
                dados = resposta.json()
                secoes = dados.get("sections") or []
                partes_texto: list[str] = []
                for secao in secoes:
                    titulo_secao = str(secao.get("title") or "").strip()
                    corpo_limpo = _limpar_html(str(secao.get("body") or ""))
                    if corpo_limpo:
                        partes_texto.append(f"## {titulo_secao}\n{corpo_limpo}" if titulo_secao else corpo_limpo)

                skills_lista = [str(skill).strip() for skill in (dados.get("skillsNames") or []) if skill]
                if skills_lista:
                    partes_texto.append(f"Skills: {', '.join(skills_lista)}")

                if partes_texto:
                    texto_completo = "\n\n".join(partes_texto)
                    job.descricao_completa = texto_completo
                    job.descricao_resumida = texto_completo[:300]
        except Exception:
            pass
        return job
