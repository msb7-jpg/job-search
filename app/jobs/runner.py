from app.core.config import Settings
from app.core.logging import logger
from app.jobs.facade import JobsPipelineFacade
from app.models.job import JobItem
from app.profiles.base import Profile
from app.profiles.predefined import DEFAULT_PROFILES


def executar_busca_jobs_direta(
    settings: Settings | None = None,
    profiles: list[Profile] = DEFAULT_PROFILES,
) -> tuple[list[JobItem], list[JobItem]]:
    config = settings or Settings(
        usar_proxy=False,
        enriquecer_detalhes=False,
    )

    logger.info("=" * 80)
    logger.info("💼 INICIANDO BUSCA DIRETA DE JOBS (LINKEDIN)")
    logger.info(
        f"⚙️ Config: Recência={config.filtro_tempo.descricao} [{config.filtro_tempo.value}] | "
        f"Proxy={config.usar_proxy} | Enriquecimento={config.enriquecer_detalhes} | "
        f"Remoto={config.apenas_remoto} | Senioridade={config.senioridade_filtro}"
    )
    logger.info(f"👤 Perfis Ativos: {[perfil.display_name for perfil in profiles]}")
    logger.info("=" * 80)

    facade = JobsPipelineFacade(
        settings=config,
        profiles=profiles,
    )
    jobs_nacionais, jobs_internacionais = facade.run()

    total_encontrado = len(jobs_nacionais) + len(jobs_internacionais)
    logger.info("=" * 80)
    logger.info("📊 RESUMO DE VAGAS ENCONTRADAS")
    logger.info(f"Total Geral: {total_encontrado} vagas")
    logger.info(f"  🇧🇷 Nacionais (Brasil): {len(jobs_nacionais)}")
    logger.info(f"  🌐 Internacionais (Gringa): {len(jobs_internacionais)}")
    logger.info("=" * 80)

    if jobs_nacionais:
        logger.info("\n--- Amostra de Vagas Nacionais ---")
        for indice, job in enumerate(jobs_nacionais[:5], 1):
            logger.info(f"{indice}. {job.titulo} | {job.empresa} | {job.localizacao} -> {job.link}")

    if jobs_internacionais:
        logger.info("\n--- Amostra de Vagas Internacionais ---")
        for indice, job in enumerate(jobs_internacionais[:5], 1):
            logger.info(f"{indice}. {job.titulo} | {job.empresa} | {job.localizacao} -> {job.link}")

    return jobs_nacionais, jobs_internacionais


if __name__ == "__main__":
    executar_busca_jobs_direta()
