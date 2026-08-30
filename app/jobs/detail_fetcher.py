from concurrent.futures import ThreadPoolExecutor

from bs4 import BeautifulSoup

from app.core.logging import logger
from app.jobs.classifiers import classificar_modelo_trabalho, classificar_senioridade
from app.models.job import JobItem
from app.shared.http.client import requisicao_com_rotacao


def obter_descricao_completa(job_id: str) -> str:
    if not job_id or job_id.startswith("job_"):
        return ""
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
    try:
        response = requisicao_com_rotacao(url)
        if response and response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            desc_elem = soup.find("div", class_="show-more-less-html__markup") or soup.find("section", class_="description")
            if desc_elem:
                return desc_elem.get_text(separator="\n").strip()
    except Exception as e:
        logger.debug(f"[JOBS-DETAIL] Erro ao extrair descrição de {job_id}: {e}")
    return ""

def enriquecer_job_com_descricao(job: JobItem, apenas_remoto: bool = True, senioridade_filtro: str = "JUNIOR") -> JobItem:
    desc = obter_descricao_completa(job.job_id)
    job.descricao_completa = desc
    job.modelo_trabalho = classificar_modelo_trabalho(job.titulo, job.localizacao, desc, padrao_remoto=apenas_remoto)
    job.senioridade = classificar_senioridade(job.titulo, desc, padrao_junior=(senioridade_filtro == "JUNIOR"))
    return job

def enriquecer_jobs_em_lote(jobs: list[JobItem], max_workers: int = 10, apenas_remoto: bool = True, senioridade_filtro: str = "JUNIOR") -> list[JobItem]:
    logger.info(f"[JOBS-DETAIL] Iniciando Aggressive Fetch para {len(jobs)} vagas (threads={max_workers})...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        jobs_enriquecidos = list(executor.map(
            lambda job: enriquecer_job_com_descricao(job, apenas_remoto, senioridade_filtro),
            jobs
        ))
    logger.info(f"[JOBS-DETAIL] Aggressive Fetch concluído para {len(jobs_enriquecidos)} vagas.")
    return jobs_enriquecidos
