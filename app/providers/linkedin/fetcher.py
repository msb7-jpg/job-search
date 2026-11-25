import hashlib
import re
import urllib.parse

from bs4 import BeautifulSoup

from app.core.logging import logger
from app.models.enums import SeniorityEnum, TimeFilterEnum, WorkModelEnum
from app.models.job import JobItem
from app.shared.classifiers import classificar_modelo_trabalho, classificar_senioridade
from app.shared.html_formatter import html_to_markdown
from proxy_pool.client import requisicao_com_rotacao


def buscar_vagas_linkedin_guest(
    keywords: str,
    location: str,
    filtro_tempo: TimeFilterEnum,
    apenas_remoto: bool,
    senioridade_filtro: str,
    usar_proxy: bool,
    timeout: int,
    max_retries: int,
    max_paginas: int = 10,
) -> list[JobItem]:
    vagas: list[JobItem] = []
    filtro_remoto_param = "&f_WT=2" if apenas_remoto else ""
    filtro_senioridade_param = "&f_E=2" if senioridade_filtro == "JUNIOR" else ""
    tpr_param = f"&f_TPR={filtro_tempo.linkedin_tpr}" if filtro_tempo.linkedin_tpr else ""

    logger.debug(f"[LINKEDIN] Buscando '{keywords}' em '{location}'...")

    for pagina in range(max_paginas):
        start = pagina * 10
        url = (
            f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            f"?keywords={urllib.parse.quote(keywords)}&location={urllib.parse.quote(location)}"
            f"{tpr_param}{filtro_remoto_param}{filtro_senioridade_param}&start={start}"
        )
        try:
            response = requisicao_com_rotacao(
                url,
                usar_proxy=usar_proxy,
                timeout=timeout,
                max_retries=max_retries,
            )
            if not response or response.status_code != 200:
                break

            soup = BeautifulSoup(response.text, "html.parser")
            items = soup.find_all("li")
            if not items:
                break

            vagas_na_pagina = 0
            for item_li in items:
                title_tag = item_li.find("h3", class_="base-search-card__title")
                company_tag = item_li.find("h4", class_="base-search-card__subtitle")
                location_tag = item_li.find("span", class_="job-search-card__location")
                link_tag = item_li.find("a", class_="base-card__full-link")
                date_tag = item_li.find("time", class_="job-search-card__listdate") or item_li.find(
                    "time", class_="job-search-card__listdate--new"
                )

                if title_tag and link_tag:
                    vagas_na_pagina += 1
                    href_raw = link_tag.get("href")
                    href_str = href_raw if isinstance(href_raw, str) else ""
                    if not href_str:
                        continue
                    link = href_str.split("?")[0]
                    titulo = title_tag.get_text().strip()
                    empresa = company_tag.get_text().strip() if company_tag else "N/A"
                    localizacao_txt = location_tag.get_text().strip() if location_tag else location
                    data_postagem = date_tag.get_text().strip() if date_tag else "Recente"

                    match_id = re.search(r"-(\d+)(?:\?|$)", link)
                    url_hash = hashlib.sha256(link.encode("utf-8")).hexdigest()[:16]
                    job_id = match_id.group(1) if match_id else f"job_{url_hash}"

                    vagas.append(
                        JobItem(
                            job_id=job_id,
                            provider="LinkedIn",
                            titulo=titulo,
                            empresa=empresa,
                            localizacao=localizacao_txt,
                            data_postagem=data_postagem,
                            senioridade=(SeniorityEnum.JUNIOR if senioridade_filtro == "JUNIOR" else SeniorityEnum.NAO_ESPECIFICADO),
                            modelo_trabalho=(WorkModelEnum.REMOTO if apenas_remoto else WorkModelEnum.NAO_ESPECIFICADO),
                            link=link,
                            descricao_resumida=f"{empresa} - {localizacao_txt}",
                            descricao_completa="",
                        )
                    )

            if vagas_na_pagina < 10:
                break
        except Exception as excecao:
            logger.warning(f"[LINKEDIN] Erro ao buscar '{keywords}' em '{location}': {excecao}")
            break

    logger.info(f"[LINKEDIN] '{keywords}' em '{location}': {len(vagas)} vagas extraídas.")
    return vagas


def obter_descricao_completa_linkedin(
    job_id: str,
    usar_proxy: bool,
    timeout: int,
    max_retries: int,
) -> str:
    if not job_id or job_id.startswith("job_"):
        return ""
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
    try:
        response = requisicao_com_rotacao(
            url,
            usar_proxy=usar_proxy,
            timeout=timeout,
            max_retries=max_retries,
        )
        if response and response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            desc_elem = (
                soup.find("div", class_="show-more-less-html__markup")
                or soup.find("div", class_="description__text")
                or soup.find("section", class_="description")
                or soup.find("div", class_="decorated-job-posting__details")
            )
            if desc_elem:
                return html_to_markdown(str(desc_elem))
    except Exception as excecao:
        logger.debug(f"[LINKEDIN-DETAIL] Erro ao extrair descrição de {job_id}: {excecao}")
    return ""


def enriquecer_vaga_linkedin(
    job: JobItem,
    apenas_remoto: bool,
    senioridade_filtro: str,
    usar_proxy: bool,
    timeout: int,
    max_retries: int,
) -> JobItem:
    descricao = obter_descricao_completa_linkedin(
        job.job_id,
        usar_proxy=usar_proxy,
        timeout=timeout,
        max_retries=max_retries,
    )
    job.descricao_completa = descricao
    job.modelo_trabalho = classificar_modelo_trabalho(job.titulo, job.localizacao, descricao, padrao_remoto=apenas_remoto)
    job.senioridade = classificar_senioridade(job.titulo, descricao, padrao_junior=(senioridade_filtro == "JUNIOR"))
    return job
