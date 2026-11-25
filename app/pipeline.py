import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import Settings, settings as default_settings
from app.core.logging import logger
from app.core.user_config import load_search_config
from app.db import (
    JobRow,
    ScrapeRunRow,
    compute_url_hash,
    get_jobs_for_pdf,
    get_pending_llm_jobs,
    init_db,
    save_evaluation,
    upsert_scraped_jobs,
)
from app.exporters.pdf_exporter import gerar_relatorio_qualificadas_pdf, gerar_relatorio_rejeitadas_pdf
from app.matchers.llm_matcher import filtrar_vagas_com_llm_em_lote
from app.matchers.resume_matcher import avaliar_compatibilidade, gerar_diagnostico_descarte_keywords
from app.models.enums import SeniorityEnum, WorkModelEnum
from app.models.job import JobItem
from app.profiles.base import Profile
from app.profiles.predefined import DEFAULT_PROFILE
from app.providers import ProviderContext, ProviderRegistry
from app.shared.classifiers import avaliar_pre_filtro_job_bruto, classificar_modelo_trabalho, classificar_senioridade
from proxy_pool import rotator


def _inicializar_proxy_pool(settings: Settings) -> None:
    if settings.usar_proxy:
        logger.info("⚙️ Inicializando pool de proxies...")
        rotator.tier_a_cache_path = settings.proxy_tier_a_cache_file
        rotator.inicializar_pool(
            max_concurrency=settings.max_concurrency_proxies,
            strategy=settings.estrategia_proxy,
        )
    else:
        logger.info("⚡ Execução em modo direto ativada (sem proxy).")


def _coletar_vagas_concorrente(
    settings: Settings,
    profile: Profile,
    providers_filter: list[str] | None = None,
) -> tuple[list[JobItem], list[str], list[str]]:
    """Executa todos os provedores ativos em paralelo e retorna (vagas_unicas, nomes_provedores, erros)."""
    contexto = ProviderContext(settings=settings, profile=profile)
    provedores_ativos = ProviderRegistry.get_active_providers(settings)
    if providers_filter:
        filtro_lower = {nome.strip().lower() for nome in providers_filter}
        provedores_ativos = [prov for prov in provedores_ativos if prov.provider_name.lower() in filtro_lower]

    nomes_provedores = [prov.provider_name for prov in provedores_ativos]
    if not provedores_ativos:
        return [], [], []

    logger.info(f"🔌 Executando {len(provedores_ativos)} provedores em paralelo: {', '.join(nomes_provedores)}")
    jobs_brutos: list[JobItem] = []
    erros: list[str] = []

    with ThreadPoolExecutor(max_workers=len(provedores_ativos)) as executor:
        futuros = {executor.submit(prov.fetch_jobs, contexto): prov.provider_name for prov in provedores_ativos}
        for futuro in as_completed(futuros):
            nome_prov = futuros[futuro]
            try:
                vagas_provider = futuro.result()
                for vaga in vagas_provider:
                    vaga.provider = nome_prov
                jobs_brutos.extend(vagas_provider)
            except Exception as erro:
                msg = f"Erro no provedor '{nome_prov}': {erro}"
                logger.warning(f"⚠️ {msg}")
                erros.append(msg)

    vagas_unicas: dict[str, JobItem] = {}
    for job in jobs_brutos:
        chave = compute_url_hash(job.link or job.job_id)
        vagas_unicas[chave] = job

    jobs_coletados = list(vagas_unicas.values())
    logger.info(f"📦 [PIPELINE] Coleta concluída: {len(jobs_brutos)} brutas -> {len(jobs_coletados)} únicas.")
    return jobs_coletados, nomes_provedores, erros


def _aplicar_camada_1(
    pares: list[tuple[JobRow, JobItem]],
    settings: Settings,
    profile: Profile,
    blacklisted_companies: list[str] | None = None,
) -> tuple[list[tuple[JobRow, JobItem]], list[tuple[JobRow, JobItem]]]:
    """Aplica pré-filtro heurístico, senioridade, modalidade e score de keywords."""
    threshold = settings.threshold_minimo_match
    aprovados: list[tuple[JobRow, JobItem]] = []
    rejeitados: list[tuple[JobRow, JobItem]] = []

    for row, job_item in pares:
        if job_item.camada_descarte or job_item.motivo_descarte:
            rejeitados.append((row, job_item))
            continue

        aprovado_pre, motivo_pre = avaliar_pre_filtro_job_bruto(
            titulo=job_item.titulo,
            localizacao=job_item.localizacao,
            apenas_remoto=settings.apenas_remoto,
            senioridade_filtro=settings.senioridade_filtro,
            empresa=job_item.empresa,
            descricao=job_item.descricao_completa or job_item.descricao_resumida,
            blacklisted_companies=blacklisted_companies,
        )
        if not aprovado_pre:
            job_item.camada_descarte = "Camada 1 - Pré-Filtro Heurístico"
            job_item.motivo_descarte = f"Descarte no pré-filtro inicial: {motivo_pre}."
            rejeitados.append((row, job_item))
            continue

        texto_descricao = job_item.descricao_completa or job_item.descricao_resumida
        if texto_descricao:
            job_item.senioridade = classificar_senioridade(
                titulo=job_item.titulo,
                descricao=texto_descricao,
                padrao_junior=False,
            )
            job_item.modelo_trabalho = classificar_modelo_trabalho(
                titulo=job_item.titulo,
                localizacao=job_item.localizacao,
                descricao=texto_descricao,
                padrao_remoto=(job_item.modelo_trabalho == WorkModelEnum.REMOTO),
            )

        if settings.senioridade_filtro == "JUNIOR" and job_item.senioridade in (SeniorityEnum.SENIOR, SeniorityEnum.PLENO):
            job_item.camada_descarte = "Camada 1 - Heurística de Senioridade"
            job_item.motivo_descarte = (
                f"Senioridade classificada como {job_item.senioridade.value} (excede o limite de Júnior/Entry-Level)."
            )
            rejeitados.append((row, job_item))
            continue

        if settings.apenas_remoto and job_item.modelo_trabalho != WorkModelEnum.REMOTO:
            job_item.camada_descarte = "Camada 1 - Heurística de Local/Modelo"
            job_item.motivo_descarte = f"Modelo de trabalho classificado como {job_item.modelo_trabalho.value} (não é 100% remoto viável)."
            rejeitados.append((row, job_item))
            continue

        job_item.match_curriculo = avaliar_compatibilidade(job_item, perfil=profile)
        if job_item.match_curriculo.score_maximo >= threshold:
            aprovados.append((row, job_item))
        else:
            job_item.camada_descarte = "Camada 1 - Score de Keywords"
            job_item.motivo_descarte = gerar_diagnostico_descarte_keywords(
                item=job_item,
                match_curriculo=job_item.match_curriculo,
                threshold=threshold,
            )
            rejeitados.append((row, job_item))

    return aprovados, rejeitados


def _avaliar_e_persistir(
    session: Session,
    pares: list[tuple[JobRow, JobItem]],
    settings: Settings,
    profile: Profile,
    rotulo_lote: str,
    blacklisted_companies: list[str] | None = None,
) -> tuple[int, int, int]:
    """Executa Camada 1 + Camada 2 (LLM) e persiste os resultados no SQLite."""
    aprovados_c1, rejeitados_c1 = _aplicar_camada_1(pares, settings, profile, blacklisted_companies=blacklisted_companies)

    for row, item in rejeitados_c1:
        save_evaluation(session, row, item, llm_status="SKIPPED")

    if not aprovados_c1:
        session.commit()
        return 0, len(rejeitados_c1), 0

    item_to_row = {id(item): row for row, item in aprovados_c1}
    candidatos_llm = [item for _, item in aprovados_c1]

    if settings.usar_filtro_llm:
        aprovados_llm, rejeitados_llm, pendentes_llm = filtrar_vagas_com_llm_em_lote(
            vagas=candidatos_llm,
            settings=settings,
            rotulo_lote=rotulo_lote,
        )
        for grupo, status_llm in (
            (aprovados_llm, "APPROVED"),
            (rejeitados_llm, "REJECTED"),
            (pendentes_llm, "PENDING"),
        ):
            for item in grupo:
                save_evaluation(session, item_to_row[id(item)], item, llm_status=status_llm)
        session.commit()
        return len(aprovados_llm), len(rejeitados_c1) + len(rejeitados_llm), len(pendentes_llm)

    for row, item in aprovados_c1:
        save_evaluation(session, row, item, llm_status="APPROVED")
    session.commit()
    return len(aprovados_c1), len(rejeitados_c1), 0


def export_pdfs_from_db(settings: Settings = default_settings) -> None:
    """Gera os PDFs executivos (qualificadas e rejeitadas) a partir do SQLite."""
    engine = init_db(settings.database_path)
    with Session(engine) as session:
        qualificadas, rejeitadas = get_jobs_for_pdf(session)

    gerar_relatorio_qualificadas_pdf(vagas=qualificadas, caminho_pdf=settings.output_pdf_report)
    if rejeitadas:
        gerar_relatorio_rejeitadas_pdf(vagas_rejeitadas=rejeitadas, caminho_pdf=settings.output_rejeitadas_pdf_report)


def rejudge_pending_jobs(
    settings: Settings = default_settings,
    profile: Profile | None = None,
    skip_pdf: bool = False,
) -> tuple[int, int, int]:
    """Reavalia todas as vagas com llm_status='PENDING' no SQLite sem re-executar scrapers."""
    user_config = load_search_config()
    effective_settings = user_config.apply_to_settings(settings)
    effective_profile = profile or user_config.to_profile()

    engine = init_db(effective_settings.database_path)
    with Session(engine) as session:
        pendentes = get_pending_llm_jobs(session)
        if not pendentes:
            logger.info("✅ Nenhuma vaga com avaliação LLM pendente no banco.")
            return 0, 0, 0

        logger.info(f"🔄 Reavaliando {len(pendentes)} vagas pendentes...")
        aprovadas, rejeitadas, ainda_pendentes = _avaliar_e_persistir(
            session, pendentes, effective_settings, effective_profile, "Rejudge Pendentes", user_config.blacklisted_companies
        )

    if not skip_pdf:
        export_pdfs_from_db(effective_settings)
    return aprovadas, rejeitadas, ainda_pendentes


def run_pipeline(
    settings: Settings = default_settings,
    profile: Profile | None = None,
    providers_filter: list[str] | None = None,
    skip_pdf: bool = False,
    use_user_config: bool = True,
) -> dict[str, int]:
    """Executa o pipeline completo: coleta -> deduplicação SQLite -> filtro/LLM -> PDF."""
    user_config = load_search_config() if use_user_config else None
    effective_settings = user_config.apply_to_settings(settings) if user_config else settings
    effective_profile = profile or (user_config.to_profile() if user_config else DEFAULT_PROFILE)
    blacklisted = user_config.blacklisted_companies if user_config else None

    engine = init_db(effective_settings.database_path)
    _inicializar_proxy_pool(effective_settings)

    with Session(engine) as session:
        run_row = ScrapeRunRow(started_at=datetime.now(UTC), status="RUNNING")
        session.add(run_row)
        session.commit()

        try:
            jobs_coletados, nomes_provedores, erros = _coletar_vagas_concorrente(
                settings=effective_settings,
                profile=effective_profile,
                providers_filter=providers_filter,
            )
            pares_novos, ja_avaliadas = upsert_scraped_jobs(session, jobs_coletados)
            logger.info(f"🗄️ [SQLITE] {len(pares_novos)} novas/pendentes | {len(ja_avaliadas)} já avaliadas (puladas).")

            aprovadas, rejeitadas, pendentes = _avaliar_e_persistir(
                session, pares_novos, effective_settings, effective_profile, "Pipeline Unificado", blacklisted
            )

            run_row.finished_at = datetime.now(UTC)
            run_row.status = "COMPLETED"
            run_row.providers_json = json.dumps(nomes_provedores, ensure_ascii=False)
            run_row.total_fetched, run_row.total_new = len(jobs_coletados), len(pares_novos)
            run_row.total_approved, run_row.total_rejected = aprovadas, rejeitadas
            run_row.error_log = "\n".join(erros)
            session.commit()
        except Exception as erro:
            run_row.finished_at, run_row.status, run_row.error_log = datetime.now(UTC), "FAILED", str(erro)
            session.commit()
            raise

    if not skip_pdf:
        export_pdfs_from_db(effective_settings)

    logger.info(f"✨ Pipeline finalizado! Aprovadas: {aprovadas} | Rejeitadas: {rejeitadas} | Pendentes: {pendentes}")
    return {
        "fetched": len(jobs_coletados),
        "new_or_pending": len(pares_novos),
        "skipped_existing": len(ja_avaliadas),
        "approved": aprovadas,
        "rejected": rejeitadas,
        "pending_llm": pendentes,
    }
