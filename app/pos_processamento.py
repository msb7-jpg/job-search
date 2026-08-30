import json
from pathlib import Path

from app.core.config import settings
from app.core.logging import logger
from app.facades.job_search_facade import JobSearchMasterFacade
from app.models.job import JobItem
from app.models.post import PostItem


def processar_vagas_com_curriculo(caminho_json: str | Path | None = None) -> None:
    logger.info("Executando pós-processamento standalone...")
    target_path = Path(caminho_json) if caminho_json else settings.output_raw_json

    if not target_path.exists():
        logger.error(f"Arquivo '{target_path}' não encontrado.")
        return

    with open(target_path, encoding="utf-8") as f:
        data = json.load(f)

    vagas_brutas = data.get("vagas", [])
    jobs_nac, jobs_int, posts_nac, posts_int = [], [], [], []

    for item in vagas_brutas:
        tipo = item.get("tipo", "jobs")
        escopo = item.get("escopo", "nacional")
        if tipo == "post":
            post_obj = PostItem(**item)
            if escopo == "nacional":
                posts_nac.append(post_obj)
            else:
                posts_int.append(post_obj)
        else:
            job_obj = JobItem(**item)
            if escopo == "nacional":
                jobs_nac.append(job_obj)
            else:
                jobs_int.append(job_obj)

    facade = JobSearchMasterFacade(settings=settings)
    output = facade.executar_pos_processamento(jobs_nac, jobs_int, posts_nac, posts_int)
    facade.exportar_resultados(output)

if __name__ == "__main__":
    processar_vagas_com_curriculo()
