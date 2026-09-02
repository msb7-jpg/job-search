from concurrent.futures import ThreadPoolExecutor

from bs4 import BeautifulSoup

from app.core.logging import logger
from app.jobs.classifiers import classificar_modelo_trabalho, classificar_senioridade
from app.models.job import JobItem
from app.shared.http.client import requisicao_com_rotacao


def obter_descricao_completa(
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
            desc_elem = soup.find("div", class_="show-more-less-html__markup") or soup.find(
                "section", class_="description"
            )
            if desc_elem:
                return desc_elem.get_text(separator="\n").strip()
    except Exception as excecao:
        logger.debug(f"[JOBS-DETAIL] Erro ao extrair descrição de {job_id}: {excecao}")
    return ""


def enriquecer_job_com_descricao(
    job: JobItem,
    apenas_remoto: bool,
    senioridade_filtro: str,
    usar_proxy: bool,
    timeout: int,
    max_retries: int,
) -> JobItem:
    descricao = obter_descricao_completa(
        job.job_id,
        usar_proxy=usar_proxy,
        timeout=timeout,
        max_retries=max_retries,
    )
    job.descricao_completa = descricao
    job.modelo_trabalho = classificar_modelo_trabalho(
        job.titulo, job.localizacao, descricao, padrao_remoto=apenas_remoto
    )
    job.senioridade = classificar_senioridade(
        job.titulo, descricao, padrao_junior=(senioridade_filtro == "JUNIOR")
    )
    return job


def classificar_job_rapido(
    job: JobItem,
    apenas_remoto: bool,
    senioridade_filtro: str,
) -> JobItem:
    job.modelo_trabalho = classificar_modelo_trabalho(
        job.titulo, job.localizacao, "", padrao_remoto=apenas_remoto
    )
    job.senioridade = classificar_senioridade(
        job.titulo, "", padrao_junior=(senioridade_filtro == "JUNIOR")
    )
    return job


def classificar_jobs_rapido_em_lote(
    jobs: list[JobItem],
    apenas_remoto: bool,
    senioridade_filtro: str,
) -> list[JobItem]:
    logger.info(f"[JOBS-DETAIL] Classificação rápida sem fetch profundo para {len(jobs)} vagas.")
    return [
        classificar_job_rapido(
            job,
            apenas_remoto=apenas_remoto,
            senioridade_filtro=senioridade_filtro,
        )
        for job in jobs
    ]


def enriquecer_jobs_em_lote(
    jobs: list[JobItem],
    max_workers: int,
    apenas_remoto: bool,
    senioridade_filtro: str,
    usar_proxy: bool,
    timeout: int,
    max_retries: int,
) -> list[JobItem]:
    logger.info(f"[JOBS-DETAIL] Iniciando Aggressive Fetch para {len(jobs)} vagas (threads={max_workers})...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        jobs_enriquecidos = list(
            executor.map(
                lambda job: enriquecer_job_com_descricao(
                    job,
                    apenas_remoto=apenas_remoto,
                    senioridade_filtro=senioridade_filtro,
                    usar_proxy=usar_proxy,
                    timeout=timeout,
                    max_retries=max_retries,
                ),
                jobs,
            )
        )
    logger.info(f"[JOBS-DETAIL] Aggressive Fetch concluído para {len(jobs_enriquecidos)} vagas.")
    return jobs_enriquecidos
