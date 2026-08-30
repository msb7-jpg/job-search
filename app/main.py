from app.core.config import Settings
from app.core.logging import logger
from app.facades.job_search_facade import JobSearchMasterFacade


def main() -> None:
    settings = Settings()
    logger.info(
        f"Iniciando Job Search Automation (Recência: {settings.filtro_tempo} | "
        f"Remoto: {settings.apenas_remoto} | Senioridade: {settings.senioridade_filtro})"
    )

    facade = JobSearchMasterFacade(settings=settings)
    facade.run()

if __name__ == "__main__":
    main()
