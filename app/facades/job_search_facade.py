from app.ats.facade import AtsPipelineFacade
from app.core.config import Settings, settings as default_settings
from app.core.logging import logger
from app.exporters.json_exporter import salvar_dados_brutos_json, salvar_dados_processados_json
from app.exporters.markdown_exporter import gerar_relatorio_markdown
from app.exporters.pdf_exporter import (
    gerar_relatorio_qualificadas_pdf,
    gerar_relatorio_rejeitadas_markdown,
    gerar_relatorio_rejeitadas_pdf,
)
from app.jobs.classifiers import (
    avaliar_pre_filtro_job_bruto,
    classificar_modelo_trabalho,
    classificar_senioridade,
)
from app.jobs.facade import JobsPipelineFacade
from app.matchers.llm_matcher import filtrar_vagas_com_llm_em_lote
from app.matchers.resume_matcher import (
    avaliar_compatibilidade,
    gerar_diagnostico_descarte_keywords,
)
from app.models.enums import SeniorityEnum, WorkModelEnum
from app.models.job import JobItem
from app.models.post import PostItem
from app.models.report import ProcessedDataOutput, ScopeContainer
from app.notifiers.telegram_notifier import TelegramNotifier
from app.posts.facade import PostsPipelineFacade
from app.profiles.base import Profile
from app.profiles.predefined import DEFAULT_PROFILES
from app.shared.http.proxy_rotator import rotator


class JobSearchMasterFacade:
    def __init__(
        self,
        settings: Settings = default_settings,
        profiles: list[Profile] = DEFAULT_PROFILES,
    ) -> None:
        self.settings = settings
        self.profiles = profiles
        self.jobs_facade = JobsPipelineFacade(
            settings=self.settings,
            profiles=self.profiles,
        )
        self.posts_facade = PostsPipelineFacade(
            settings=self.settings,
            profiles=self.profiles,
        )
        self.ats_facade = AtsPipelineFacade(
            settings=self.settings,
            profiles=self.profiles,
        )

    def inicializar_infraestrutura(self) -> None:
        if self.settings.usar_proxy:
            logger.info("⚙️ Inicializando infraestrutura e pool de proxies...")
            rotator.inicializar_pool(
                max_concurrency=self.settings.max_concurrency_proxies,
                strategy=self.settings.estrategia_proxy,
            )
        else:
            logger.info("⚡ Execução em modo direto ativada (sem proxy).")

    def executar_extracao(
        self,
    ) -> tuple[list[JobItem], list[JobItem], list[PostItem], list[PostItem]]:
        logger.info("🚀 [FASE 1/3] Executando extração de oportunidades...")

        # Coleta de Jobs
        jobs_nac, jobs_int = self.jobs_facade.run()

        # Coleta de Posts (Condicional / Standby)
        if self.settings.buscar_posts:
            posts_nac, posts_int = self.posts_facade.run()
        else:
            logger.info("💬 [POSTS-PIPELINE] Extração de posts do LinkedIn em standby (buscar_posts=False).")
            posts_nac, posts_int = [], []

        # Exportação Bruta
        todos_itens_brutos = [j.model_dump() for j in jobs_nac + jobs_int] + [p.model_dump() for p in posts_nac + posts_int]
        dados_brutos = {
            "termo_pesquisado": "Vagas Formais & Posts LinkedIn (BR & Gringa)",
            "filtro_tempo": self.settings.filtro_tempo,
            "apenas_remoto": self.settings.apenas_remoto,
            "senioridade_filtrada": self.settings.senioridade_filtro,
            "total_extraido": len(todos_itens_brutos),
            "vagas": todos_itens_brutos,
        }
        salvar_dados_brutos_json(dados_brutos, self.settings.output_raw_json)

        return jobs_nac, jobs_int, posts_nac, posts_int

    def _filtrar_e_pontuar_lote_jobs(self, jobs_lote: list[JobItem]) -> tuple[list[JobItem], list[JobItem]]:
        threshold = self.settings.threshold_minimo_match
        aprovados: list[JobItem] = []
        rejeitados: list[JobItem] = []

        for job_item in jobs_lote:
            aprovado_pre, motivo_pre = avaliar_pre_filtro_job_bruto(
                titulo=job_item.titulo,
                localizacao=job_item.localizacao,
                apenas_remoto=self.settings.apenas_remoto,
                senioridade_filtro=self.settings.senioridade_filtro,
                empresa=job_item.empresa,
                descricao=job_item.descricao_completa or job_item.descricao_resumida,
            )
            if not aprovado_pre:
                job_item.camada_descarte = "Camada 1 - Pré-Filtro Heurístico"
                job_item.motivo_descarte = f"Descarte no pré-filtro inicial: {motivo_pre}."
                rejeitados.append(job_item)
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

            if self.settings.senioridade_filtro == "JUNIOR" and job_item.senioridade in (
                SeniorityEnum.SENIOR,
                SeniorityEnum.PLENO,
            ):
                job_item.camada_descarte = "Camada 1 - Heurística de Senioridade"
                job_item.motivo_descarte = (
                    f"Senioridade classificada como {job_item.senioridade.value} (excede o limite de Júnior/Entry-Level)."
                )
                rejeitados.append(job_item)
                continue

            if self.settings.apenas_remoto and job_item.modelo_trabalho != WorkModelEnum.REMOTO:
                job_item.camada_descarte = "Camada 1 - Heurística de Local/Modelo"
                job_item.motivo_descarte = (
                    f"Modelo de trabalho classificado como {job_item.modelo_trabalho.value} (não é 100% remoto viável)."
                )
                rejeitados.append(job_item)
                continue

            job_item.match_curriculo = avaliar_compatibilidade(job_item, perfis=self.profiles)
            scores = (
                [match.score_porcentagem for match in job_item.match_curriculo.perfis.values()]
                if job_item.match_curriculo and job_item.match_curriculo.perfis
                else []
            )
            if any(score >= threshold for score in scores):
                aprovados.append(job_item)
            else:
                job_item.camada_descarte = "Camada 1 - Score de Keywords"
                job_item.motivo_descarte = gerar_diagnostico_descarte_keywords(
                    item=job_item,
                    match_curriculo=job_item.match_curriculo,
                    threshold=threshold,
                )
                rejeitados.append(job_item)

        return aprovados, rejeitados

    def executar_pos_processamento(
        self,
        jobs_nac: list[JobItem],
        jobs_int: list[JobItem],
        posts_nac: list[PostItem],
        posts_int: list[PostItem],
    ) -> ProcessedDataOutput:
        logger.info("🎯 [FASE 2/3] Executando avaliação de compatibilidade de currículo (Matcher)...")
        threshold = self.settings.threshold_minimo_match

        # Processar Jobs Nacionais e Internacionais (Heurística + Keyword Match)
        jobs_nac_aprovados, jobs_nac_rejeitados = self._filtrar_e_pontuar_lote_jobs(jobs_nac)
        jobs_int_aprovados, jobs_int_rejeitados = self._filtrar_e_pontuar_lote_jobs(jobs_int)

        todas_rejeitadas: list[JobItem] = []
        todas_rejeitadas.extend(jobs_nac_rejeitados)
        todas_rejeitadas.extend(jobs_int_rejeitados)

        # Processar Posts Nacionais (Posts são todos mantidos)
        posts_nac_processados: list[PostItem] = []
        for post_item in posts_nac:
            post_item.match_curriculo = avaliar_compatibilidade(post_item, perfis=self.profiles)
            posts_nac_processados.append(post_item)

        # Processar Posts Internacionais
        posts_int_processados: list[PostItem] = []
        for post_item in posts_int:
            post_item.match_curriculo = avaliar_compatibilidade(post_item, perfis=self.profiles)
            posts_int_processados.append(post_item)

        # Ordenar cada categoria por maior match primeiro (com desempate por total de skills encontradas)
        def extrair_chave_match(item: JobItem | PostItem) -> tuple[int, int]:
            if not item.match_curriculo:
                return (0, 0)
            return (
                item.match_curriculo.score_maximo,
                item.match_curriculo.total_skills_maximo,
            )

        jobs_nac_aprovados.sort(key=extrair_chave_match, reverse=True)
        jobs_int_aprovados.sort(key=extrair_chave_match, reverse=True)
        posts_nac_processados.sort(key=extrair_chave_match, reverse=True)
        posts_int_processados.sort(key=extrair_chave_match, reverse=True)

        # 2ª Camada: Filtro Semântico via LLM Local (lcpp / gemini-bridge)
        if self.settings.usar_filtro_llm:
            if jobs_nac_aprovados:
                jobs_nac_aprovados, rejeitadas_llm_nac = filtrar_vagas_com_llm_em_lote(
                    vagas=jobs_nac_aprovados,
                    settings=self.settings,
                    rotulo_lote="LinkedIn Nacional",
                )
                todas_rejeitadas.extend(rejeitadas_llm_nac)
                jobs_nac_aprovados.sort(key=extrair_chave_match, reverse=True)

            if jobs_int_aprovados:
                jobs_int_aprovados, rejeitadas_llm_int = filtrar_vagas_com_llm_em_lote(
                    vagas=jobs_int_aprovados,
                    settings=self.settings,
                    rotulo_lote="LinkedIn Internacional",
                )
                todas_rejeitadas.extend(rejeitadas_llm_int)
                jobs_int_aprovados.sort(key=extrair_chave_match, reverse=True)

        total_aprovados = len(jobs_nac_aprovados) + len(jobs_int_aprovados) + len(posts_nac_processados) + len(posts_int_processados)

        return ProcessedDataOutput(
            filtro_threshold_minimo=threshold,
            total_aprovados=total_aprovados,
            total_rejeitados=len(todas_rejeitadas),
            nacional=ScopeContainer(jobs=jobs_nac_aprovados, post=posts_nac_processados),
            internacional=ScopeContainer(jobs=jobs_int_aprovados, post=posts_int_processados),
            rejeitadas=todas_rejeitadas,
        )

    def exportar_resultados(self, output: ProcessedDataOutput) -> None:
        logger.info("📊 [FASE 3/3] Exportando relatórios JSON, Markdown e PDFs Executivos...")
        salvar_dados_processados_json(output, self.settings.output_processed_json)
        gerar_relatorio_markdown(output, self.settings.output_markdown_report)

        # Gerar PDFs Executivos (Qualificadas e Rejeitadas)
        todas_qualificadas = output.nacional.jobs + output.internacional.jobs
        gerar_relatorio_qualificadas_pdf(
            vagas=todas_qualificadas,
            caminho_pdf=self.settings.output_pdf_report,
        )
        if output.rejeitadas:
            gerar_relatorio_rejeitadas_pdf(
                vagas_rejeitadas=output.rejeitadas,
                caminho_pdf=self.settings.output_rejeitadas_pdf_report,
            )
            gerar_relatorio_rejeitadas_markdown(
                vagas_rejeitadas=output.rejeitadas,
                caminho_md=self.settings.output_rejeitadas_markdown_report,
            )

    def run(self) -> ProcessedDataOutput:
        self.inicializar_infraestrutura()
        jobs_nac, jobs_int, posts_nac, posts_int = self.executar_extracao()
        output = self.executar_pos_processamento(jobs_nac, jobs_int, posts_nac, posts_int)
        self.exportar_resultados(output)

        output_ats = None
        if self.settings.buscar_ats:
            logger.info("🏢 [ATS] Iniciando pipeline de vagas Gupy e InHire integrado...")
            output_ats = self.ats_facade.run(notificar_telegram=False)

            # Regenerar PDFs unificados com todas as vagas (LinkedIn + ATS)
            todas_qualificadas = output.nacional.jobs + output.internacional.jobs + (output_ats.vagas if output_ats else [])
            todas_rejeitadas = output.rejeitadas + (output_ats.rejeitadas if output_ats else [])

            gerar_relatorio_qualificadas_pdf(
                vagas=todas_qualificadas,
                caminho_pdf=self.settings.output_pdf_report,
            )
            if todas_rejeitadas:
                gerar_relatorio_rejeitadas_pdf(
                    vagas_rejeitadas=todas_rejeitadas,
                    caminho_pdf=self.settings.output_rejeitadas_pdf_report,
                )
                gerar_relatorio_rejeitadas_markdown(
                    vagas_rejeitadas=todas_rejeitadas,
                    caminho_md=self.settings.output_rejeitadas_markdown_report,
                )

        if self.settings.enviar_telegram:
            notifier = TelegramNotifier(settings=self.settings)
            notifier.enviar_relatorio_completo(output_ats=output_ats, output_linkedin=output)

        logger.info(f"✨ Pipeline finalizado com {output.total_aprovados} oportunidades qualificadas no LinkedIn!")
        return output
