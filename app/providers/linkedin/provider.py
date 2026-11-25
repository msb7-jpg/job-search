from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import ClassVar

from tqdm import tqdm

from app.core.logging import logger
from app.models.job import JobItem
from app.providers.base import JobProviderStrategy, ProviderContext
from app.providers.linkedin.fetcher import buscar_vagas_linkedin_guest, enriquecer_vaga_linkedin
from app.providers.registry import ProviderRegistry


@ProviderRegistry.register
class LinkedInProvider(JobProviderStrategy):
    provider_name: ClassVar[str] = "LinkedIn"
    badge_colors: ClassVar[tuple[str, str]] = ("#0a66c2", "#ffffff")
    supports_enrichment: ClassVar[bool] = True

    def enrichment_workers(self, context: ProviderContext) -> int:
        return context.settings.max_workers_jobs

    def search_jobs(self, context: ProviderContext) -> list[JobItem]:
        queries_vistas: set[str] = set()
        queries: list[str] = []
        for query in context.profile.queries_jobs:
            query_limpa = query.strip()
            if query_limpa and query_limpa.lower() not in queries_vistas:
                queries_vistas.add(query_limpa.lower())
                queries.append(query_limpa)

        if not queries:
            return []

        location = context.settings.localizacao_linkedin
        workers = min(8, max(2, len(queries)))
        vagas_coletadas: list[JobItem] = []

        logger.info(f"💼 [LINKEDIN] Buscando {len(queries)} queries de tecnologia em '{location}'...")
        with (
            ThreadPoolExecutor(max_workers=workers) as executor,
            tqdm(total=len(queries), desc="💼 [LINKEDIN] Queries", unit="query") as barra,
        ):
            futuros = {
                executor.submit(
                    buscar_vagas_linkedin_guest,
                    keywords=keyword,
                    location=location,
                    filtro_tempo=context.settings.filtro_tempo,
                    apenas_remoto=context.settings.apenas_remoto,
                    senioridade_filtro=context.settings.senioridade_filtro,
                    usar_proxy=context.settings.usar_proxy,
                    timeout=context.settings.http_timeout,
                    max_retries=context.settings.http_max_retries,
                    max_paginas=context.settings.max_paginas_jobs,
                ): keyword
                for keyword in queries
            }
            for futuro in as_completed(futuros):
                keyword = futuros[futuro]
                try:
                    vagas_coletadas.extend(futuro.result())
                except Exception as erro:
                    logger.warning(f"⚠️ [LINKEDIN] Erro na query '{keyword}': {erro}")
                finally:
                    barra.update(1)

        return vagas_coletadas

    def enrich_job(self, job: JobItem, context: ProviderContext) -> JobItem | None:
        return enriquecer_vaga_linkedin(
            job=job,
            apenas_remoto=context.settings.apenas_remoto,
            senioridade_filtro=context.settings.senioridade_filtro,
            usar_proxy=context.settings.usar_proxy,
            timeout=context.settings.http_timeout,
            max_retries=context.settings.http_max_retries,
        )
