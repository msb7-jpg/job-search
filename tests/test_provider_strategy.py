import unittest
from typing import ClassVar

from app.core.config import Settings
from app.models.enums import SeniorityEnum, WorkModelEnum
from app.models.job import JobItem
from app.profiles.predefined import DEFAULT_PROFILE
from app.providers import JobProviderStrategy, ProviderContext, ProviderRegistry
from app.providers.ciandt import extrair_vagas_ciandt_html
from app.providers.fullstack import converter_item_fullstack


class TestProviderStrategyAndOcp(unittest.TestCase):
    def test_builtin_providers_registered(self) -> None:
        settings = Settings()
        ativos = ProviderRegistry.get_active_providers(settings)
        nomes = {prov.provider_name for prov in ativos}
        self.assertIn("LinkedIn", nomes)
        self.assertIn("Gupy", nomes)
        self.assertIn("InHire", nomes)
        self.assertIn("CI&T", nomes)
        self.assertIn("FullStack", nomes)

    def test_provedores_desabilitados_filtering(self) -> None:
        settings = Settings(provedores_desabilitados=["gupy", "CI&T"])
        ativos = ProviderRegistry.get_active_providers(settings)
        nomes = {prov.provider_name for prov in ativos}
        self.assertNotIn("Gupy", nomes)
        self.assertNotIn("CI&T", nomes)
        self.assertIn("LinkedIn", nomes)
        self.assertIn("FullStack", nomes)

    def test_template_method_search_prefilter_and_enrich_lifecycle(self) -> None:
        @ProviderRegistry.register
        class CustomPortalProvider(JobProviderStrategy):
            provider_name: ClassVar[str] = "CustomPortal"
            badge_colors: ClassVar[tuple[str, str]] = ("#123456", "#ffffff")
            supports_enrichment: ClassVar[bool] = True

            def search_jobs(self, context: ProviderContext) -> list[JobItem]:
                return [
                    JobItem(
                        job_id="custom_jr",
                        titulo="Python Developer Junior",
                        empresa="Custom Co",
                        localizacao="Brasil",
                        modelo_trabalho=WorkModelEnum.REMOTO,
                        senioridade=SeniorityEnum.JUNIOR,
                        link="https://custom.example.com/jobs/1",
                    ),
                    JobItem(
                        job_id="custom_adm",
                        titulo="Assistente Administrativo",
                        empresa="Custom Co",
                        localizacao="Brasil",
                        modelo_trabalho=WorkModelEnum.REMOTO,
                        senioridade=SeniorityEnum.JUNIOR,
                        link="https://custom.example.com/jobs/2",
                    ),
                ]

            def enrich_job(self, job: JobItem, context: ProviderContext) -> JobItem | None:
                job.descricao_completa = "Descrição enriquecida: Python Django FastAPI PostgreSQL Docker"
                return job

        try:
            self.assertEqual(ProviderRegistry.get_badge_colors("CustomPortal"), ("#123456", "#ffffff"))
            provider = CustomPortalProvider()
            context = ProviderContext(settings=Settings(enriquecer_detalhes=True), profile=DEFAULT_PROFILE)
            vagas = provider.fetch_jobs(context)

            # A vaga não-TI é barrada no filtro flexível de título antes de enriquecer e retida para auditoria
            self.assertEqual(len(vagas), 2)
            vagas_por_id = {vaga.job_id: vaga for vaga in vagas}

            vaga_jr = vagas_por_id["custom_jr"]
            self.assertEqual(vaga_jr.provider, "CustomPortal")
            self.assertIn("Descrição enriquecida", vaga_jr.descricao_completa)
            self.assertIsNone(vaga_jr.motivo_descarte)

            vaga_adm = vagas_por_id["custom_adm"]
            self.assertEqual(vaga_adm.provider, "CustomPortal")
            self.assertEqual(vaga_adm.descricao_completa, "")
            self.assertEqual(vaga_adm.camada_descarte, "Camada 0 - Filtro Flexível de Título")
            self.assertIsNotNone(vaga_adm.motivo_descarte)
        finally:
            ProviderRegistry._providers.pop("customportal", None)

    def test_extrair_vagas_ciandt_html(self) -> None:
        html_amostra = """
        <div class="opprtunity-item" id="opportunity-1">
          <span class="sr-only filters-item">País_Brazil Local_Brazil Tipo_de_contrato_Homeoffice Workplace_type_Remote</span>
          <div class="wp-block-cit-block-ciandt-short-text"><span>Brazil - Brazil</span></div>
          <h2 class="ciandt-heading">Junior Python Developer, Brazil</h2>
          <a href="/br/pt-br/carreiras/oportunidades/candidate-se?opportunity=70ef0c61-f0de-422c-9adb-54e39f7eabd9">Candidate-se</a>
        </div>
        <div class="opprtunity-item" id="opportunity-2">
          <span class="sr-only filters-item">País_Brazil Local_Brazil Workplace_type_Remote</span>
          <h2 class="ciandt-heading">Senior Data Architect, Brazil</h2>
          <a href="/br/pt-br/carreiras/oportunidades/candidate-se?opportunity=99999999">Candidate-se</a>
        </div>
        """
        vagas = extrair_vagas_ciandt_html(
            conteudo_html=html_amostra,
            termos_interesse=["python", "developer"],
            apenas_remoto=True,
            senioridade_filtro="JUNIOR",
        )
        self.assertEqual(len(vagas), 1)
        self.assertEqual(vagas[0].provider, "CI&T")
        self.assertEqual(vagas[0].job_id, "ciandt_70ef0c61-f0de-422c-9adb-54e39f7eabd9")
        self.assertEqual(vagas[0].modelo_trabalho, WorkModelEnum.REMOTO)

    def test_converter_item_fullstack(self) -> None:
        item_valido = {
            "id": "abc-123",
            "jobTitle": "Python & React Developer",
            "isPublished": True,
            "city": "Recife",
            "state": "PE",
            "region": "Brazil",
            "linkedInSeniority": "Entry level",
            "linkedInWorkplaceType": "Remote",
            "skillsNames": ["Python", "FastAPI", "React"],
        }
        vaga = converter_item_fullstack(
            item=item_valido,
            termos_interesse=["python"],
            apenas_remoto=True,
            senioridade_filtro="JUNIOR",
        )
        self.assertIsNotNone(vaga)
        assert vaga is not None
        self.assertEqual(vaga.provider, "FullStack")
        self.assertEqual(vaga.senioridade, SeniorityEnum.JUNIOR)
        self.assertEqual(vaga.modelo_trabalho, WorkModelEnum.REMOTO)
        self.assertIn("FastAPI", vaga.descricao_completa)


if __name__ == "__main__":
    unittest.main()
