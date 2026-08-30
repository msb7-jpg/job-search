from app.core.config import Settings, settings as default_settings
from app.core.logging import logger
from app.exporters.json_exporter import salvar_dados_brutos_json, salvar_dados_processados_json
from app.exporters.markdown_exporter import gerar_relatorio_markdown
from app.jobs.facade import JobsPipelineFacade
from app.matchers.resume_matcher import avaliar_compatibilidade
from app.models.job import JobItem
from app.models.post import PostItem
from app.models.report import ProcessedDataOutput, ScopeContainer
from app.posts.facade import PostsPipelineFacade
from app.shared.http.proxy_rotator import rotator


class JobSearchMasterFacade:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or default_settings
        self.jobs_facade = JobsPipelineFacade(settings=self.settings)
        self.posts_facade = PostsPipelineFacade(settings=self.settings)

    def inicializar_infraestrutura(self) -> None:
        logger.info("⚙️ Inicializando infraestrutura e pool de proxies...")
        rotator.inicializar_pool(max_concurrency=self.settings.max_concurrency_proxies)

    def executar_extracao(self) -> tuple[list[JobItem], list[JobItem], list[PostItem], list[PostItem]]:
        logger.info("🚀 [FASE 1/3] Executando extração concorrente de Vagas e Posts...")

        # Coleta de Jobs
        jobs_nac, jobs_int = self.jobs_facade.run()

        # Coleta de Posts
        posts_nac, posts_int = self.posts_facade.run()

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

    def executar_pos_processamento(
        self,
        jobs_nac: list[JobItem],
        jobs_int: list[JobItem],
        posts_nac: list[PostItem],
        posts_int: list[PostItem],
    ) -> ProcessedDataOutput:
        logger.info("🎯 [FASE 2/3] Executando avaliação de compatibilidade de currículo (Matcher)...")
        threshold = self.settings.threshold_minimo_match

        # Processar Jobs Nacionais
        jobs_nac_aprovados: list[JobItem] = []
        for j in jobs_nac:
            j.match_curriculo = avaliar_compatibilidade(j)
            if j.match_curriculo.backend.score_porcentagem >= threshold or j.match_curriculo.fullstack.score_porcentagem >= threshold:
                jobs_nac_aprovados.append(j)

        # Processar Jobs Internacionais
        jobs_int_aprovados: list[JobItem] = []
        for j in jobs_int:
            j.match_curriculo = avaliar_compatibilidade(j)
            if j.match_curriculo.backend.score_porcentagem >= threshold or j.match_curriculo.fullstack.score_porcentagem >= threshold:
                jobs_int_aprovados.append(j)

        # Processar Posts Nacionais (Posts são todos mantidos)
        posts_nac_processados: list[PostItem] = []
        for p in posts_nac:
            p.match_curriculo = avaliar_compatibilidade(p)
            posts_nac_processados.append(p)

        # Processar Posts Internacionais
        posts_int_processados: list[PostItem] = []
        for p in posts_int:
            p.match_curriculo = avaliar_compatibilidade(p)
            posts_int_processados.append(p)

        total_aprovados = len(jobs_nac_aprovados) + len(jobs_int_aprovados) + len(posts_nac_processados) + len(posts_int_processados)

        return ProcessedDataOutput(
            filtro_threshold_minimo=threshold,
            total_aprovados=total_aprovados,
            nacional=ScopeContainer(jobs=jobs_nac_aprovados, post=posts_nac_processados),
            internacional=ScopeContainer(jobs=jobs_int_aprovados, post=posts_int_processados),
        )

    def exportar_resultados(self, output: ProcessedDataOutput) -> None:
        logger.info("📊 [FASE 3/3] Exportando relatórios JSON e Markdown...")
        salvar_dados_processados_json(output, self.settings.output_processed_json)
        gerar_relatorio_markdown(output, self.settings.output_markdown_report)

    def run(self) -> ProcessedDataOutput:
        self.inicializar_infraestrutura()
        jobs_nac, jobs_int, posts_nac, posts_int = self.executar_extracao()
        output = self.executar_pos_processamento(jobs_nac, jobs_int, posts_nac, posts_int)
        self.exportar_resultados(output)
        logger.info(f"✨ Pipeline finalizado com {output.total_aprovados} oportunidades qualificadas!")
        return output
