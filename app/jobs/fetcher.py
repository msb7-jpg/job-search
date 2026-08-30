import re
import urllib.parse

from bs4 import BeautifulSoup

from app.core.logging import logger
from app.models.enums import ItemTypeEnum, ScopeEnum, SeniorityEnum, WorkModelEnum
from app.models.job import JobItem
from app.shared.http.client import requisicao_com_rotacao


def buscar_vagas_linkedin_guest(
    keywords: str,
    location: str,
    scope: ScopeEnum,
    filtro_tempo: str = "r604800",
    apenas_remoto: bool = True,
    senioridade_filtro: str = "JUNIOR",
    max_paginas: int = 3,
) -> list[JobItem]:
    vagas: list[JobItem] = []
    filtro_remoto_param = "&f_WT=2" if apenas_remoto else ""
    filtro_senioridade_param = "&f_E=2" if senioridade_filtro == "JUNIOR" else ""

    logger.debug(f"[JOBS-FETCHER] Buscando '{keywords}' em '{location}' (Escopo: {scope})...")

    for pagina in range(max_paginas):
        start = pagina * 25
        url = (
            f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            f"?keywords={urllib.parse.quote(keywords)}&location={urllib.parse.quote(location)}"
            f"&f_TPR={filtro_tempo}{filtro_remoto_param}{filtro_senioridade_param}&start={start}"
        )
        try:
            response = requisicao_com_rotacao(url)
            if not response or response.status_code != 200:
                break

            soup = BeautifulSoup(response.text, "html.parser")
            items = soup.find_all("li")
            if not items:
                break

            for li in items:
                title_tag = li.find("h3", class_="base-search-card__title")
                company_tag = li.find("h4", class_="base-search-card__subtitle")
                location_tag = li.find("span", class_="job-search-card__location")
                link_tag = li.find("a", class_="base-card__full-link")
                date_tag = li.find("time", class_="job-search-card__listdate") or li.find("time", class_="job-search-card__listdate--new")

                if title_tag and link_tag:
                    link = link_tag["href"].split("?")[0]
                    titulo = title_tag.get_text().strip()
                    empresa = company_tag.get_text().strip() if company_tag else "N/A"
                    localizacao_txt = location_tag.get_text().strip() if location_tag else location
                    data_postagem = date_tag.get_text().strip() if date_tag else "Recente"

                    match_id = re.search(r"-(\d+)(?:\?|$)", link)
                    job_id = match_id.group(1) if match_id else f"job_{hash(link) & 0xFFFFFFFF}"

                    vagas.append(JobItem(
                        job_id=job_id,
                        tipo=ItemTypeEnum.JOB,
                        escopo=scope,
                        titulo=titulo,
                        empresa=empresa,
                        localizacao=localizacao_txt,
                        data_postagem=data_postagem,
                        senioridade=SeniorityEnum.JUNIOR if senioridade_filtro == "JUNIOR" else SeniorityEnum.NAO_ESPECIFICADO,
                        modelo_trabalho=WorkModelEnum.REMOTO if apenas_remoto else WorkModelEnum.NAO_ESPECIFICADO,
                        link=link,
                        descricao_resumida=f"{empresa} - {localizacao_txt}",
                        descricao_completa=""
                    ))
        except Exception as e:
            logger.warning(f"[JOBS-FETCHER] Erro ao buscar '{keywords}' em '{location}': {e}")
            break

    logger.info(f"[JOBS-FETCHER] '{keywords}' em '{location}': {len(vagas)} vagas extraídas.")
    return vagas
