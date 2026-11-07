from app.ats.facade import AtsPipelineFacade
from app.core.config import Settings
from app.core.logging import logger
from app.models.report import AtsReportOutput
from app.profiles.base import Profile
from app.profiles.predefined import DEFAULT_PROFILES


def executar_busca_ats_direta(
    settings: Settings | None = None,
    profiles: list[Profile] = DEFAULT_PROFILES,
) -> AtsReportOutput:
    config = settings or Settings()

    logger.info("=" * 80)
    logger.info("🏢 INICIANDO BUSCA DE VAGAS ATS (GUPY + INHIRE)")
    logger.info(
        f"⚙️ Config: Recência={config.filtro_tempo_ats.descricao} [{config.filtro_tempo_ats.value}] | "
        f"Remoto={config.apenas_remoto} | Senioridade={config.senioridade_filtro} | "
        f"Enriquecer InHire={config.enriquecer_detalhes_inhire}"
    )
    logger.info(f"👤 Perfis Ativos: {[perfil.display_name for perfil in profiles]}")
    logger.info(f"📄 Arquivo do Relatório: {config.output_ats_markdown_report}")
    logger.info("=" * 80)

    facade = AtsPipelineFacade(settings=config, profiles=profiles)
    output = facade.run()

    logger.info("=" * 80)
    logger.info("📊 RESUMO DE VAGAS ATS ENCONTRADAS")
    logger.info(f"Total Qualificado: {output.total_aprovados} vagas")
    logger.info(f"  🟣 Gupy: {output.total_gupy}")
    logger.info(f"  🟢 InHire: {output.total_inhire}")
    logger.info("=" * 80)

    if output.vagas:
        logger.info("\n--- Top 5 Vagas com Maior Match ---")
        for indice, vaga in enumerate(output.vagas[:5], 1):
            score = vaga.match_curriculo.score_maximo if vaga.match_curriculo else 0
            logger.info(
                f"{indice}. [{vaga.plataforma}] {vaga.titulo} (Match: {score}%) | {vaga.empresa} | {vaga.localizacao} -> {vaga.link}"
            )

    return output


if __name__ == "__main__":
    executar_busca_ats_direta()
