import json
from pathlib import Path

from app.ats.facade import AtsPipelineFacade
from app.core.config import Settings, settings as default_settings
from app.core.logging import logger
from app.exporters.json_exporter import salvar_dados_brutos_json
from app.exporters.pdf_exporter import (
    gerar_relatorio_qualificadas_pdf,
    gerar_relatorio_rejeitadas_markdown,
    gerar_relatorio_rejeitadas_pdf,
)
from app.facades.job_search_facade import JobSearchMasterFacade
from app.models.job import JobItem
from app.models.post import PostItem
from app.models.report import AtsReportOutput
from app.notifiers.telegram_notifier import TelegramNotifier
from app.profiles.base import Profile
from app.profiles.predefined import DEFAULT_PROFILES


def processar_vagas_ats_com_curriculo(
    caminho_json: str | Path | None = None,
    settings: Settings = default_settings,
    profiles: list[Profile] = DEFAULT_PROFILES,
) -> AtsReportOutput | None:
    logger.info("Executando pós-processamento standalone de ATS (Gupy + InHire)...")
    target_path = Path(caminho_json) if caminho_json else settings.output_ats_raw_json

    if not target_path.exists():
        logger.info(f"📂 Arquivo bruto de ATS '{target_path}' não encontrado.")
        return None

    with open(target_path, encoding="utf-8") as f:
        data = json.load(f)

    vagas_brutas = [JobItem(**item) for item in data.get("vagas", [])]
    facade_ats = AtsPipelineFacade(settings=settings, profiles=profiles)
    output_ats = facade_ats.executar_pos_processamento(vagas_brutas)
    facade_ats.exportar_resultados(output_ats)
    return output_ats


def _separar_itens_brutos(
    vagas_brutas: list[dict],
) -> tuple[list[JobItem], list[JobItem], list[PostItem], list[PostItem]]:
    jobs_nac: list[JobItem] = []
    jobs_int: list[JobItem] = []
    posts_nac: list[PostItem] = []
    posts_int: list[PostItem] = []

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

    return jobs_nac, jobs_int, posts_nac, posts_int


def processar_vagas_com_curriculo(
    caminho_json: str | Path | None = None,
    settings: Settings = default_settings,
    profiles: list[Profile] = DEFAULT_PROFILES,
) -> None:
    logger.info("Executando pós-processamento standalone de LinkedIn...")
    target_path = Path(caminho_json) if caminho_json else settings.output_raw_json

    if not target_path.exists():
        logger.error(f"Arquivo '{target_path}' não encontrado.")
        return

    with open(target_path, encoding="utf-8") as f:
        data = json.load(f)

    vagas_brutas = data.get("vagas", [])
    jobs_nac, jobs_int, posts_nac, posts_int = _separar_itens_brutos(vagas_brutas)

    facade = JobSearchMasterFacade(settings=settings, profiles=profiles)
    output = facade.executar_pos_processamento(jobs_nac, jobs_int, posts_nac, posts_int)
    facade.exportar_resultados(output)

    # Reprocessar ATS também se o arquivo existir
    output_ats = None
    if settings.output_ats_raw_json.exists():
        output_ats = processar_vagas_ats_com_curriculo(settings=settings, profiles=profiles)

    # Gerar PDFs Executivos e Relatórios de Rejeitadas Consolidados (LinkedIn + ATS)
    todas_aprovadas: list[JobItem] = []
    todas_aprovadas.extend(output.nacional.jobs)
    todas_aprovadas.extend(output.internacional.jobs)
    if output_ats and output_ats.vagas:
        todas_aprovadas.extend(output_ats.vagas)

    def extrair_score(vaga: JobItem) -> int:
        return vaga.match_curriculo.score_maximo if vaga.match_curriculo else 0

    todas_aprovadas.sort(key=extrair_score, reverse=True)

    todas_rejeitadas: list[JobItem] = []
    todas_rejeitadas.extend(output.rejeitadas)
    if output_ats and output_ats.rejeitadas:
        todas_rejeitadas.extend(output_ats.rejeitadas)

    logger.info(
        f"📑 [CONSOLIDADO] Gerando relatórios executivos em PDF "
        f"(Qualificadas: {len(todas_aprovadas)}, Rejeitadas: {len(todas_rejeitadas)})..."
    )
    gerar_relatorio_qualificadas_pdf(
        vagas=todas_aprovadas,
        caminho_pdf=settings.output_pdf_report,
    )

    if todas_rejeitadas:
        gerar_relatorio_rejeitadas_pdf(
            vagas_rejeitadas=todas_rejeitadas,
            caminho_pdf=settings.output_rejeitadas_pdf_report,
        )
        gerar_relatorio_rejeitadas_markdown(
            vagas_rejeitadas=todas_rejeitadas,
            caminho_md=settings.output_rejeitadas_markdown_report,
        )
        salvar_dados_brutos_json(
            {
                "total_rejeitadas": len(todas_rejeitadas),
                "vagas": [vaga.model_dump() for vaga in todas_rejeitadas],
            },
            settings.output_rejeitadas_json,
        )

    # Disparar notificação Telegram consolidada se ativado
    if settings.enviar_telegram:
        notifier = TelegramNotifier(settings=settings)
        notifier.enviar_relatorio_completo(output_ats=output_ats, output_linkedin=output)


if __name__ == "__main__":
    processar_vagas_com_curriculo()
