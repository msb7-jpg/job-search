from typing import ClassVar

from app.models.job import JobItem
from app.providers.base import JobProviderStrategy, ProviderContext
from app.providers.inhire.fetcher import buscar_vagas_candidatas_inhire, enriquecer_vaga_inhire
from app.providers.registry import ProviderRegistry


@ProviderRegistry.register
class InHireProvider(JobProviderStrategy):
    provider_name: ClassVar[str] = "InHire"
    badge_colors: ClassVar[tuple[str, str]] = ("#059669", "#ffffff")
    supports_enrichment: ClassVar[bool] = True

    def is_enabled(self, settings) -> bool:
        return super().is_enabled(settings)

    def enrichment_workers(self, context: ProviderContext) -> int:
        return context.settings.max_workers_ats

    def search_jobs(self, context: ProviderContext) -> list[JobItem]:
        termos_vistos: set[str] = set()
        termos_inhire: list[str] = []
        for termo in context.profile.termos_cargo_inhire:
            termo_limpo = termo.strip().lower()
            if termo_limpo and termo_limpo not in termos_vistos:
                termos_vistos.add(termo_limpo)
                termos_inhire.append(termo_limpo)

        return buscar_vagas_candidatas_inhire(
            caminho_tenants=context.settings.inhire_tenants_file,
            termos_cargo_inhire=termos_inhire,
            apenas_remoto=context.settings.apenas_remoto,
            senioridade_filtro=context.settings.senioridade_filtro,
            max_workers=context.settings.max_workers_ats,
            timeout=context.settings.http_timeout,
        )

    def enrich_job(self, job: JobItem, context: ProviderContext) -> JobItem | None:
        if not context.settings.enriquecer_detalhes_inhire:
            return job
        return enriquecer_vaga_inhire(
            vaga=job,
            filtro_tempo=context.settings.filtro_tempo_ats,
            timeout=context.settings.http_timeout,
        )
