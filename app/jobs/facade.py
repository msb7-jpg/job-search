from app.core.config import Settings, settings as default_settings
from app.core.logging import logger
from app.jobs.classifiers import pre_filtrar_job_bruto
from app.jobs.detail_fetcher import enriquecer_jobs_em_lote
from app.jobs.fetcher import buscar_vagas_linkedin_guest
from app.jobs.queries import Gringas, Nacionais
from app.models.enums import ScopeEnum, SeniorityEnum, WorkModelEnum
from app.models.job import JobItem


class JobsPipelineFacade:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or default_settings

    def run(self) -> tuple[list[JobItem], list[JobItem]]:
        logger.info("💼 [JOBS-PIPELINE] Iniciando extração de vagas formais...")

        # 1. Busca Nacionais
        jobs_nac_brutos: list[JobItem] = []
        for keyword, location in Nacionais.TERMOS_JOBS:
            jobs_nac_brutos.extend(buscar_vagas_linkedin_guest(
                keywords=keyword,
                location=location,
                scope=ScopeEnum.NACIONAL,
                filtro_tempo=self.settings.filtro_tempo,
                apenas_remoto=self.settings.apenas_remoto,
                senioridade_filtro=self.settings.senioridade_filtro,
            ))

        # 2. Busca Internacionais (Gringa)
        jobs_int_brutos: list[JobItem] = []
        for keyword, location in Gringas.TERMOS_JOBS:
            jobs_int_brutos.extend(buscar_vagas_linkedin_guest(
                keywords=keyword,
                location=location,
                scope=ScopeEnum.INTERNACIONAL,
                filtro_tempo=self.settings.filtro_tempo,
                apenas_remoto=self.settings.apenas_remoto,
                senioridade_filtro=self.settings.senioridade_filtro,
            ))

        # 3. Deduplicação por Link
        jobs_nac_dict = {j.link: j for j in jobs_nac_brutos}
        jobs_int_dict = {j.link: j for j in jobs_int_brutos}

        todos_jobs_brutos = list(jobs_nac_dict.values()) + list(jobs_int_dict.values())
        logger.info(f"💼 [JOBS-PIPELINE] Vagas brutas coletadas: {len(todos_jobs_brutos)} (BR: {len(jobs_nac_dict)}, Gringa: {len(jobs_int_dict)})")

        # 4. Pré-filtragem
        jobs_pre_filtrados = [
            j for j in todos_jobs_brutos
            if pre_filtrar_job_bruto(
                j.titulo,
                j.localizacao,
                apenas_remoto=self.settings.apenas_remoto,
                senioridade_filtro=self.settings.senioridade_filtro,
            )
        ]
        descartados_pre = len(todos_jobs_brutos) - len(jobs_pre_filtrados)
        logger.info(f"💼 [JOBS-PIPELINE] Descartados no pré-filtro: {descartados_pre} | Restantes para Aggressive Fetch: {len(jobs_pre_filtrados)}")

        # 5. Aggressive Fetch de Descrição Completa e Classificação
        jobs_processados = enriquecer_jobs_em_lote(
            jobs_pre_filtrados,
            max_workers=self.settings.max_workers_jobs,
            apenas_remoto=self.settings.apenas_remoto,
            senioridade_filtro=self.settings.senioridade_filtro,
        )

        # 6. Pós-filtragem rigorosa pós-fetch
        if self.settings.apenas_remoto:
            jobs_processados = [j for j in jobs_processados if j.modelo_trabalho == WorkModelEnum.REMOTO]
        if self.settings.senioridade_filtro == "JUNIOR":
            jobs_processados = [
                j for j in jobs_processados
                if j.senioridade in [SeniorityEnum.JUNIOR, SeniorityEnum.ESTAGIO, SeniorityEnum.NAO_ESPECIFICADO]
            ]

        nac_finais = [j for j in jobs_processados if j.escopo == ScopeEnum.NACIONAL]
        int_finais = [j for j in jobs_processados if j.escopo == ScopeEnum.INTERNACIONAL]

        logger.info(f"💼 [JOBS-PIPELINE] Vagas aprovadas pós-classificação: Nacional={len(nac_finais)}, Internacional={len(int_finais)}")
        return nac_finais, int_finais
