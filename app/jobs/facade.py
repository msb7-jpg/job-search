from tqdm import tqdm

from app.core.config import Settings
from app.core.logging import logger
from app.jobs.classifiers import avaliar_pre_filtro_job_bruto
from app.jobs.detail_fetcher import classificar_jobs_rapido_em_lote, enriquecer_jobs_em_lote
from app.jobs.fetcher import buscar_vagas_linkedin_guest
from app.models.enums import ScopeEnum, SeniorityEnum, WorkModelEnum
from app.models.job import JobItem
from app.profiles.base import Profile


class JobsPipelineFacade:
    def __init__(
        self,
        settings: Settings,
        profiles: list[Profile],
    ) -> None:
        self.settings = settings
        self.profiles = profiles

    def _obter_queries_nacionais(self) -> list[tuple[str, str]]:
        queries_vistas: set[tuple[str, str]] = set()
        queries_ordenadas: list[tuple[str, str]] = []
        for perfil in self.profiles:
            for query_tupla in perfil.queries_jobs_nacionais:
                if query_tupla not in queries_vistas:
                    queries_vistas.add(query_tupla)
                    queries_ordenadas.append(query_tupla)
        return queries_ordenadas

    def _obter_queries_internacionais(self) -> list[tuple[str, str]]:
        queries_vistas: set[tuple[str, str]] = set()
        queries_ordenadas: list[tuple[str, str]] = []
        for perfil in self.profiles:
            for query_tupla in perfil.queries_jobs_internacionais:
                if query_tupla not in queries_vistas:
                    queries_vistas.add(query_tupla)
                    queries_ordenadas.append(query_tupla)
        return queries_ordenadas

    def _buscar_vagas_por_queries(
        self,
        queries: list[tuple[str, str]],
        scope: ScopeEnum,
        barra_progresso: tqdm,
    ) -> list[JobItem]:
        rotulo_escopo = "Brasil" if scope == ScopeEnum.NACIONAL else "Gringa"
        jobs_coletados: list[JobItem] = []
        for keyword, location in queries:
            encontradas = buscar_vagas_linkedin_guest(
                keywords=keyword,
                location=location,
                scope=scope,
                filtro_tempo=self.settings.filtro_tempo,
                apenas_remoto=self.settings.apenas_remoto,
                senioridade_filtro=self.settings.senioridade_filtro,
                usar_proxy=self.settings.usar_proxy,
                timeout=self.settings.http_timeout,
                max_retries=self.settings.http_max_retries,
            )
            logger.info(
                f"💼 [JOBS-SEARCH] Query: '{keyword}' em '{location}' ({rotulo_escopo}) -> {len(encontradas)} vagas encontradas"
            )
            jobs_coletados.extend(encontradas)
            barra_progresso.update(1)
        return jobs_coletados

    def _executar_pre_filtro(
        self,
        todos_jobs_brutos: list[JobItem],
        total_brutas_extraidas: int,
        total_nacionais_unicas: int,
        total_internacionais_unicas: int,
        duplicadas_descartadas: int,
    ) -> list[JobItem]:
        jobs_pre_filtrados: list[JobItem] = []
        descartados_senioridade = 0
        descartados_presencial = 0

        for job in todos_jobs_brutos:
            aprovado, motivo = avaliar_pre_filtro_job_bruto(
                titulo=job.titulo,
                localizacao=job.localizacao,
                apenas_remoto=self.settings.apenas_remoto,
                senioridade_filtro=self.settings.senioridade_filtro,
            )
            if aprovado:
                jobs_pre_filtrados.append(job)
            elif motivo == "senioridade_incompativel":
                descartados_senioridade += 1
            elif motivo == "modelo_presencial":
                descartados_presencial += 1

        descartados_pre_total = len(todos_jobs_brutos) - len(jobs_pre_filtrados)

        logger.info(
            f"💼 [JOBS-PIPELINE] Vagas brutas coletadas: {total_brutas_extraidas} "
            f"(Únicas: {len(todos_jobs_brutos)} [BR: {total_nacionais_unicas}, Gringa: {total_internacionais_unicas}], "
            f"Duplicadas descartadas: {duplicadas_descartadas})"
        )
        logger.info(
            f"💼 [JOBS-PIPELINE] Descarte no Pré-Filtro Inicial: {descartados_pre_total} vagas descartadas "
            f"({descartados_senioridade} por senioridade incompatível, {descartados_presencial} por modelo presencial/híbrido) | "
            f"Restantes para enriquecimento/classificação: {len(jobs_pre_filtrados)}"
        )
        return jobs_pre_filtrados

    def _executar_pos_filtro(
        self,
        jobs_processados: list[JobItem],
    ) -> tuple[list[JobItem], list[JobItem]]:
        total_antes_pos_filtro = len(jobs_processados)
        if self.settings.apenas_remoto:
            jobs_processados = [
                job for job in jobs_processados if job.modelo_trabalho == WorkModelEnum.REMOTO
            ]
        descartados_pos_remoto = total_antes_pos_filtro - len(jobs_processados)

        total_antes_pos_senioridade = len(jobs_processados)
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
        descartados_pos_senioridade = total_antes_pos_senioridade - len(jobs_processados)
        descartados_pos_total = descartados_pos_remoto + descartados_pos_senioridade

        nac_finais = [job for job in jobs_processados if job.escopo == ScopeEnum.NACIONAL]
        int_finais = [job for job in jobs_processados if job.escopo == ScopeEnum.INTERNACIONAL]

        if descartados_pos_total > 0:
            logger.info(
                f"💼 [JOBS-PIPELINE] Descarte no Pós-Filtro Rigoroso: {descartados_pos_total} vagas descartadas "
                f"({descartados_pos_remoto} por modelo de trabalho não-remoto, {descartados_pos_senioridade} por senioridade não-júnior)"
            )

        logger.info(
            f"💼 [JOBS-PIPELINE] Vagas finais aprovadas: Nacional={len(nac_finais)}, "
            f"Internacional={len(int_finais)} (Total: {len(nac_finais) + len(int_finais)})"
        )
        return nac_finais, int_finais

    def run(self) -> tuple[list[JobItem], list[JobItem]]:
        queries_nacionais = self._obter_queries_nacionais()
        queries_internacionais = self._obter_queries_internacionais()
        total_queries = len(queries_nacionais) + len(queries_internacionais)

        logger.info(
            f"💼 [JOBS-PIPELINE] Iniciando extração de vagas formais para "
            f"{len(self.profiles)} perfis ({', '.join(perfil.name for perfil in self.profiles)}) | "
            f"Total de {total_queries} queries [Filtro: {self.settings.filtro_tempo.descricao} ({self.settings.filtro_tempo.value})]..."
        )

        # 1. Execução de Queries com Barra de Progresso
        with tqdm(total=total_queries, desc="💼 [JOBS] Buscando Queries LinkedIn", unit="query") as barra_progresso:
            jobs_nacionais_brutos = self._buscar_vagas_por_queries(
                queries=queries_nacionais,
                scope=ScopeEnum.NACIONAL,
                barra_progresso=barra_progresso,
            )
            jobs_internacionais_brutos = self._buscar_vagas_por_queries(
                queries=queries_internacionais,
                scope=ScopeEnum.INTERNACIONAL,
                barra_progresso=barra_progresso,
            )

        # 2. Deduplicação por Link
        total_brutas_extraidas = len(jobs_nacionais_brutos) + len(jobs_internacionais_brutos)
        jobs_nac_dict = {job.link: job for job in jobs_nacionais_brutos}
        jobs_int_dict = {job.link: job for job in jobs_internacionais_brutos}

        todos_jobs_brutos = list(jobs_nac_dict.values()) + list(jobs_int_dict.values())
        duplicadas_descartadas = total_brutas_extraidas - len(todos_jobs_brutos)

        # 3. Pré-filtragem com Contabilização de Descartes
        jobs_pre_filtrados = self._executar_pre_filtro(
            todos_jobs_brutos=todos_jobs_brutos,
            total_brutas_extraidas=total_brutas_extraidas,
            total_nacionais_unicas=len(jobs_nac_dict),
            total_internacionais_unicas=len(jobs_int_dict),
            duplicadas_descartadas=duplicadas_descartadas,
        )

        # 4. Classificação (Enriquecimento agressivo ou classificação rápida)
        if self.settings.enriquecer_detalhes:
            jobs_processados = enriquecer_jobs_em_lote(
                jobs_pre_filtrados,
                max_workers=self.settings.max_workers_jobs,
                apenas_remoto=self.settings.apenas_remoto,
                senioridade_filtro=self.settings.senioridade_filtro,
                usar_proxy=self.settings.usar_proxy,
                timeout=self.settings.http_timeout,
                max_retries=self.settings.http_max_retries,
            )
        else:
            jobs_processados = classificar_jobs_rapido_em_lote(
                jobs_pre_filtrados,
                apenas_remoto=self.settings.apenas_remoto,
                senioridade_filtro=self.settings.senioridade_filtro,
            )

        # 5. Pós-filtragem rigorosa com Contabilização de Descartes
        return self._executar_pos_filtro(jobs_processados)


if __name__ == "__main__":
    from app.jobs.runner import executar_busca_jobs_direta

    executar_busca_jobs_direta()
