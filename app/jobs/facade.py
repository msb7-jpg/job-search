from app.core.config import Settings, settings as default_settings
from app.core.logging import logger
from app.jobs.classifiers import pre_filtrar_job_bruto
from app.jobs.detail_fetcher import classificar_jobs_rapido_em_lote, enriquecer_jobs_em_lote
from app.jobs.fetcher import buscar_vagas_linkedin_guest
from app.models.enums import ScopeEnum, SeniorityEnum, WorkModelEnum
from app.models.job import JobItem
from app.profiles.base import Profile
from app.profiles.predefined import DEFAULT_PROFILES


class JobsPipelineFacade:
    def __init__(
        self,
        settings: Settings | None = None,
        profiles: list[Profile] | None = None,
        usar_proxy: bool | None = None,
        enriquecer_detalhes: bool | None = None,
    ) -> None:
        self.settings = settings or default_settings
        self.profiles = profiles if profiles is not None else DEFAULT_PROFILES
        self.usar_proxy = usar_proxy if usar_proxy is not None else self.settings.usar_proxy
        self.enriquecer_detalhes = (
            enriquecer_detalhes
            if enriquecer_detalhes is not None
            else self.settings.enriquecer_detalhes
        )

    def _obter_queries_nacionais(self, perfis: list[Profile]) -> list[tuple[str, str]]:
        queries_vistas: set[tuple[str, str]] = set()
        queries_ordenadas: list[tuple[str, str]] = []
        for perfil in perfis:
            for query_tupla in perfil.queries_jobs_nacionais:
                if query_tupla not in queries_vistas:
                    queries_vistas.add(query_tupla)
                    queries_ordenadas.append(query_tupla)
        return queries_ordenadas

    def _obter_queries_internacionais(self, perfis: list[Profile]) -> list[tuple[str, str]]:
        queries_vistas: set[tuple[str, str]] = set()
        queries_ordenadas: list[tuple[str, str]] = []
        for perfil in perfis:
            for query_tupla in perfil.queries_jobs_internacionais:
                if query_tupla not in queries_vistas:
                    queries_vistas.add(query_tupla)
                    queries_ordenadas.append(query_tupla)
        return queries_ordenadas

    def run(self, profiles: list[Profile] | None = None) -> tuple[list[JobItem], list[JobItem]]:
        perfis_execucao = profiles if profiles is not None else self.profiles
        logger.info(
            f"💼 [JOBS-PIPELINE] Iniciando extração de vagas formais para "
            f"{len(perfis_execucao)} perfis ({', '.join(p.name for p in perfis_execucao)}) "
            f"[Filtro: {self.settings.filtro_tempo.descricao} ({self.settings.filtro_tempo.value})]..."
        )

        queries_nacionais = self._obter_queries_nacionais(perfis_execucao)
        queries_internacionais = self._obter_queries_internacionais(perfis_execucao)

        # 1. Busca Nacionais
        jobs_nacionais_brutos: list[JobItem] = []
        for keyword, location in queries_nacionais:
            encontradas = buscar_vagas_linkedin_guest(
                keywords=keyword,
                location=location,
                scope=ScopeEnum.NACIONAL,
                filtro_tempo=self.settings.filtro_tempo,
                apenas_remoto=self.settings.apenas_remoto,
                senioridade_filtro=self.settings.senioridade_filtro,
                usar_proxy=self.usar_proxy,
            )
            logger.info(
                f"💼 [JOBS-SEARCH] Query: '{keyword}' em '{location}' (Brasil) -> {len(encontradas)} vagas encontradas"
            )
            jobs_nacionais_brutos.extend(encontradas)

        # 2. Busca Internacionais (Gringa)
        jobs_internacionais_brutos: list[JobItem] = []
        for keyword, location in queries_internacionais:
            encontradas = buscar_vagas_linkedin_guest(
                keywords=keyword,
                location=location,
                scope=ScopeEnum.INTERNACIONAL,
                filtro_tempo=self.settings.filtro_tempo,
                apenas_remoto=self.settings.apenas_remoto,
                senioridade_filtro=self.settings.senioridade_filtro,
                usar_proxy=self.usar_proxy,
            )
            logger.info(
                f"💼 [JOBS-SEARCH] Query: '{keyword}' em '{location}' (Gringa) -> {len(encontradas)} vagas encontradas"
            )
            jobs_internacionais_brutos.extend(encontradas)

        # 3. Deduplicação por Link
        jobs_nac_dict = {job.link: job for job in jobs_nacionais_brutos}
        jobs_int_dict = {job.link: job for job in jobs_internacionais_brutos}

        todos_jobs_brutos = list(jobs_nac_dict.values()) + list(jobs_int_dict.values())
        logger.info(
            f"💼 [JOBS-PIPELINE] Vagas brutas coletadas: {len(todos_jobs_brutos)} "
            f"(BR: {len(jobs_nac_dict)}, Gringa: {len(jobs_int_dict)})"
        )

        # 4. Pré-filtragem
        jobs_pre_filtrados = [
            job
            for job in todos_jobs_brutos
            if pre_filtrar_job_bruto(
                job.titulo,
                job.localizacao,
                apenas_remoto=self.settings.apenas_remoto,
                senioridade_filtro=self.settings.senioridade_filtro,
            )
        ]
        descartados_pre = len(todos_jobs_brutos) - len(jobs_pre_filtrados)
        logger.info(
            f"💼 [JOBS-PIPELINE] Descartados no pré-filtro: {descartados_pre} | "
            f"Restantes para classificação: {len(jobs_pre_filtrados)}"
        )

        # 5. Classificação (Enriquecimento agressivo ou classificação rápida)
        if self.enriquecer_detalhes:
            jobs_processados = enriquecer_jobs_em_lote(
                jobs_pre_filtrados,
                max_workers=self.settings.max_workers_jobs,
                apenas_remoto=self.settings.apenas_remoto,
                senioridade_filtro=self.settings.senioridade_filtro,
                usar_proxy=self.usar_proxy,
            )
        else:
            jobs_processados = classificar_jobs_rapido_em_lote(
                jobs_pre_filtrados,
                apenas_remoto=self.settings.apenas_remoto,
                senioridade_filtro=self.settings.senioridade_filtro,
            )

        # 6. Pós-filtragem rigorosa
        if self.settings.apenas_remoto:
            jobs_processados = [
                job for job in jobs_processados if job.modelo_trabalho == WorkModelEnum.REMOTO
            ]
        if self.settings.senioridade_filtro == "JUNIOR":
            jobs_processados = [
                job
                for job in jobs_processados
                if job.senioridade
                in [
                    SeniorityEnum.JUNIOR,
                    SeniorityEnum.ESTAGIO,
                    SeniorityEnum.NAO_ESPECIFICADO,
                ]
            ]

        nac_finais = [job for job in jobs_processados if job.escopo == ScopeEnum.NACIONAL]
        int_finais = [job for job in jobs_processados if job.escopo == ScopeEnum.INTERNACIONAL]

        logger.info(
            f"💼 [JOBS-PIPELINE] Vagas aprovadas: Nacional={len(nac_finais)}, "
            f"Internacional={len(int_finais)} (Total: {len(nac_finais) + len(int_finais)})"
        )
        return nac_finais, int_finais


if __name__ == "__main__":
    from app.jobs.runner import executar_busca_jobs_direta

    executar_busca_jobs_direta()
