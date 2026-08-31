from app.core.config import Settings
from app.core.logging import logger
from app.jobs.facade import JobsPipelineFacade
from app.models.enums import TimeFilterEnum
from app.models.job import JobItem
from app.profiles.base import Profile
from app.profiles.predefined import DEFAULT_PROFILES


def executar_busca_jobs_direta(
    profiles: list[Profile] | None = None,
    usar_proxy: bool = False,
    enriquecer_detalhes: bool = False,
    filtro_tempo: TimeFilterEnum | str = TimeFilterEnum.ULTIMAS_24H,
    apenas_remoto: bool = True,
    senioridade_filtro: str = "JUNIOR",
) -> tuple[list[JobItem], list[JobItem]]:
    perfis = profiles if profiles is not None else DEFAULT_PROFILES
    config = Settings(
        usar_proxy=usar_proxy,
        enriquecer_detalhes=enriquecer_detalhes,
        filtro_tempo=filtro_tempo,
        apenas_remoto=apenas_remoto,
        senioridade_filtro=senioridade_filtro,
    )

    logger.info("=" * 80)
    logger.info("💼 INICIANDO BUSCA DIRETA DE JOBS (LINKEDIN)")
    logger.info(
        f"⚙️ Config: Recência={config.filtro_tempo.descricao} [{config.filtro_tempo.value}] | "
        f"Proxy={usar_proxy} | Enriquecimento={enriquecer_detalhes} | "
        f"Remoto={apenas_remoto} | Senioridade={senioridade_filtro}"
    )
    logger.info(f"👤 Perfis Ativos: {[perfil.display_name for perfil in perfis]}")
    logger.info("=" * 80)

    facade = JobsPipelineFacade(
        settings=config,
        profiles=perfis,
        usar_proxy=usar_proxy,
        enriquecer_detalhes=enriquecer_detalhes,
    )
    jobs_nacionais, jobs_internacionais = facade.run(profiles=perfis)

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
