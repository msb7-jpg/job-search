import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.exporters.pdf_exporter import gerar_relatorio_qualificadas_pdf
from app.jobs.classifiers import avaliar_pre_filtro_job_bruto
from app.models.enums import PlatformEnum, ScopeEnum, SeniorityEnum, WorkModelEnum
from app.models.job import JobItem


class TestPdfAndAiTrainerFilter(unittest.TestCase):
    def test_bloqueio_empresa_micro1(self) -> None:
        aprovado, motivo = avaliar_pre_filtro_job_bruto(
            titulo="Fullstack Software Engineer",
            localizacao="Remote",
            apenas_remoto=True,
            senioridade_filtro="JUNIOR",
            empresa="micro1",
        )
        self.assertFalse(aprovado)
        self.assertIn("Micro1", str(motivo))

        aprovado_alt, motivo_alt = avaliar_pre_filtro_job_bruto(
            titulo="Python Developer",
            localizacao="Brasil",
            apenas_remoto=True,
            senioridade_filtro="JUNIOR",
            empresa="Micro 1 AI",
        )
        self.assertFalse(aprovado_alt)
        self.assertIn("Micro 1", str(motivo_alt))

    def test_bloqueio_vaga_treinamento_ia_e_rlhf(self) -> None:
        aprovado, motivo = avaliar_pre_filtro_job_bruto(
            titulo="AI Trainer - Python & Coding",
            localizacao="Remote",
            apenas_remoto=True,
            senioridade_filtro="JUNIOR",
            empresa="Global Data Inc",
        )
        self.assertFalse(aprovado)
        self.assertIn("treinamento/avaliação de modelos de IA", str(motivo))

        aprovado_desc, motivo_desc = avaliar_pre_filtro_job_bruto(
            titulo="Software Engineer",
            localizacao="Remote",
            apenas_remoto=True,
            senioridade_filtro="JUNIOR",
            empresa="AI Labs",
            descricao="Nesta posição você atuará com RLHF e annotation de modelos de linguagem LLM.",
        )
        self.assertFalse(aprovado_desc)
        self.assertIn("treinamento/anotação de modelos de IA", str(motivo_desc))

    def test_vaga_desenvolvimento_real_aprovada_pre_filtro(self) -> None:
        aprovado, motivo = avaliar_pre_filtro_job_bruto(
            titulo="Desenvolvedor Python Júnior",
            localizacao="Remoto - Brasil",
            apenas_remoto=True,
            senioridade_filtro="JUNIOR",
            empresa="Empresa Real Tech",
            descricao="Desenvolvimento de APIs REST com Django e FastAPI.",
        )
        self.assertTrue(aprovado)
        self.assertIsNone(motivo)

    def test_pdf_header_minimal_and_candidatar_button(self) -> None:
        with TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "test_qualificadas.pdf"
            vaga = JobItem(
                job_id="101",
                titulo="Desenvolvedor Python Júnior",
                empresa="Tech Corp",
                localizacao="Remoto",
                link="https://linkedin.com/jobs/view/101",
                plataforma=PlatformEnum.LINKEDIN,
                escopo=ScopeEnum.NACIONAL,
                modelo_trabalho=WorkModelEnum.REMOTO,
                senioridade=SeniorityEnum.JUNIOR,
                descricao_completa="Atuação com desenvolvimento de backend em Python, Django e PostgreSQL para produto interno.",
            )

            # Gera o PDF
            gerado = gerar_relatorio_qualificadas_pdf([vaga], caminho_pdf=pdf_path)
            self.assertTrue(gerado.exists())
            self.assertGreater(gerado.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()
