from typing import ClassVar

from tqdm import tqdm

from app.core.logging import logger
from app.models.job import JobItem
from app.providers.base import JobProviderStrategy, ProviderContext
from app.providers.gupy.fetcher import buscar_vagas_gupy_por_query
from app.providers.registry import ProviderRegistry


@ProviderRegistry.register
class GupyProvider(JobProviderStrategy):
    provider_name: ClassVar[str] = "Gupy"
    badge_colors: ClassVar[tuple[str, str]] = ("#7c3aed", "#ffffff")
    supports_enrichment: ClassVar[bool] = False

    def search_jobs(self, context: ProviderContext) -> list[JobItem]:
        queries_vistas: set[str] = set()
        queries_gupy: list[str] = []
        for query in context.profile.queries_ats:
            query_limpa = query.strip()
            if query_limpa and query_limpa.lower() not in queries_vistas:
                queries_vistas.add(query_limpa.lower())
                queries_gupy.append(query_limpa)

        vagas_gupy: list[JobItem] = []
        logger.info(f"🟣 [GUPY] Executando busca em {len(queries_gupy)} queries no portal Gupy...")
        with tqdm(total=len(queries_gupy), desc="🟣 [GUPY] Buscando Queries", unit="query") as barra_gupy:
            for query in queries_gupy:
                encontradas = buscar_vagas_gupy_por_query(
                    termo_busca=query,
                    filtro_tempo=context.settings.filtro_tempo_ats,
                    apenas_remoto=context.settings.apenas_remoto,
                    max_paginas=context.settings.max_paginas_gupy,
                    timeout=context.settings.http_timeout,
                )
                logger.info(f"🟣 [GUPY] Query '{query}' -> {len(encontradas)} vagas encontradas")
                vagas_gupy.extend(encontradas)
                barra_gupy.update(1)

        return vagas_gupy
