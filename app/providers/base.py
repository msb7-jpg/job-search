from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import ClassVar

from tqdm import tqdm

from app.core.config import Settings
from app.core.logging import logger
from app.models.job import JobItem
from app.profiles.base import Profile
from app.shared.classifiers import avaliar_titulo_flexivel_ti


@dataclass(frozen=True)
class ProviderContext:
    settings: Settings
    profile: Profile


class JobProviderStrategy(ABC):
    """Contrato padrão (Strategy + Template Method) para provedores de vagas."""

    provider_name: ClassVar[str] = "Generic"
    badge_colors: ClassVar[tuple[str, str]] = ("#475569", "#ffffff")
    supports_enrichment: ClassVar[bool] = False

    def is_enabled(self, settings: Settings) -> bool:
        desabilitados = {nome.strip().lower() for nome in settings.provedores_desabilitados}
        return self.provider_name.lower() not in desabilitados

    def enrichment_workers(self, context: ProviderContext) -> int:
        return min(10, context.settings.max_workers_ats)

    @abstractmethod
    def search_jobs(self, context: ProviderContext) -> list[JobItem]:
        """Fase 1: Busca rápida / listagem de vagas brutas no provedor."""

    def enrich_job(self, job: JobItem, context: ProviderContext) -> JobItem | None:
        """Fase 2 (Opcional): Enriquece detalhes completos de uma vaga candidata.

        Retornar None descarta a vaga (ex: recência expirada detectada no detalhe).
        """
        return job

    def fetch_jobs(self, context: ProviderContext) -> list[JobItem]:
        """Ciclo formal padronizado: busca -> deduplicação -> filtro flexível de título -> enriquecimento concorrente."""
        vagas_brutas = self.search_jobs(context)
        if not vagas_brutas:
            return []

        # Deduplicação local por link ou job_id
        unicas_dict: dict[str, JobItem] = {}
        for vaga in vagas_brutas:
            vaga.provider = self.provider_name
            chave = vaga.link or vaga.job_id
            unicas_dict[chave] = vaga

        # Filtro flexível de título antes de enriquecer (evita falsos negativos sem gastar requests em vagas fora de TI)
        candidatas: list[JobItem] = []
        descartadas_titulo: list[JobItem] = []
        for vaga in unicas_dict.values():
            aprovado_titulo, motivo_titulo = avaliar_titulo_flexivel_ti(vaga.titulo)
            if aprovado_titulo:
                candidatas.append(vaga)
            else:
                vaga.camada_descarte = "Camada 0 - Filtro Flexível de Título"
                vaga.motivo_descarte = motivo_titulo
                descartadas_titulo.append(vaga)

        if not candidatas:
            logger.info(
                f"🔌 [{self.provider_name}] {len(unicas_dict)} vagas coletadas -> 0 elegíveis após filtro flexível de título "
                f"({len(descartadas_titulo)} descartadas)."
            )
            return descartadas_titulo

        if not (self.supports_enrichment and context.settings.enriquecer_detalhes):
            logger.info(
                f"🔌 [{self.provider_name}] {len(candidatas)} vagas elegíveis (sem enriquecimento extra; "
                f"{len(descartadas_titulo)} descartadas por título)."
            )
            return candidatas + descartadas_titulo

        workers = max(1, min(self.enrichment_workers(context), len(candidatas)))
        vagas_enriquecidas: list[JobItem] = []

        with (
            ThreadPoolExecutor(max_workers=workers) as executor,
            tqdm(total=len(candidatas), desc=f"⚡ [{self.provider_name}] Enriquecendo", unit="vaga") as barra,
        ):
            futuros = [executor.submit(self.enrich_job, vaga, context) for vaga in candidatas]
            for futuro in as_completed(futuros):
                try:
                    resultado = futuro.result()
                    if resultado is not None:
                        resultado.provider = self.provider_name
                        vagas_enriquecidas.append(resultado)
                except Exception as erro:
                    logger.debug(f"⚠️ [{self.provider_name}] Erro ao enriquecer vaga: {erro}")
                finally:
                    barra.update(1)

        logger.info(
            f"🔌 [{self.provider_name}] {len(vagas_enriquecidas)} vagas enriquecidas ({len(descartadas_titulo)} descartadas por título)."
        )
        return vagas_enriquecidas + descartadas_titulo
