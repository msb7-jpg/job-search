import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.exporters.markdown_exporter import gerar_relatorio_markdown, obter_icone_match
from app.facades.job_search_facade import JobSearchMasterFacade
from app.models.enums import MatchLevelEnum, ScopeEnum
from app.models.job import JobItem
from app.models.match import ProfileMatch, ResumeMatch
from app.models.report import ProcessedDataOutput, ScopeContainer


class TestReportOrderingAndIcons(unittest.TestCase):
    def test_obter_icone_match(self):
        self.assertEqual(obter_icone_match(100), "🔥")
        self.assertEqual(obter_icone_match(90), "🔥")
        self.assertEqual(obter_icone_match(85), "🚀")
        self.assertEqual(obter_icone_match(80), "🚀")
        self.assertEqual(obter_icone_match(75), "⚡")
        self.assertEqual(obter_icone_match(70), "⚡")
        self.assertEqual(obter_icone_match(65), "🎯")
        self.assertEqual(obter_icone_match(60), "🎯")
        self.assertEqual(obter_icone_match(50), "💡")
        self.assertEqual(obter_icone_match(30), "⚪")

    def test_resume_match_properties(self):
        match_obj = ResumeMatch(
            perfis={
                "backend": ProfileMatch(
                    nome_perfil="backend",
                    score_porcentagem=70,
                    nivel=MatchLevelEnum.ALTO,
                    habilidades_compativeis=["Python", "FastAPI"],
                ),
                "fullstack": ProfileMatch(
                    nome_perfil="fullstack",
                    score_porcentagem=95,
                    nivel=MatchLevelEnum.EXCELENTE,
                    habilidades_compativeis=["Python", "React", "Docker"],
                ),
            }
        )
        self.assertEqual(match_obj.score_maximo, 95)
        self.assertEqual(match_obj.total_skills_maximo, 3)

    def test_gerar_relatorio_markdown_sorts_descending_and_includes_icons(self):
        job_baixa = JobItem(
            job_id="1",
            titulo="Python Dev Jr",
            link="https://linkedin.com/jobs/view/1",
            escopo=ScopeEnum.NACIONAL,
            match_curriculo=ResumeMatch(
                perfis={
                    "backend": ProfileMatch(
                        nome_perfil="backend",
                        score_porcentagem=65,
                        nivel=MatchLevelEnum.ALTO,
                        habilidades_compativeis=["Python"],
                    )
                }
            ),
        )
        job_alta = JobItem(
            job_id="2",
            titulo="Python Tech Lead",
            link="https://linkedin.com/jobs/view/2",
            escopo=ScopeEnum.NACIONAL,
            match_curriculo=ResumeMatch(
                perfis={
                    "backend": ProfileMatch(
                        nome_perfil="backend",
                        score_porcentagem=100,
                        nivel=MatchLevelEnum.EXCELENTE,
                        habilidades_compativeis=["Python", "FastAPI", "Docker", "AWS"],
                    )
                }
            ),
        )
        job_media = JobItem(
            job_id="3",
            titulo="Python Dev Pleno",
            link="https://linkedin.com/jobs/view/3",
            escopo=ScopeEnum.NACIONAL,
            match_curriculo=ResumeMatch(
                perfis={
                    "backend": ProfileMatch(
                        nome_perfil="backend",
                        score_porcentagem=85,
                        nivel=MatchLevelEnum.EXCELENTE,
                        habilidades_compativeis=["Python", "FastAPI"],
                    )
                }
            ),
        )

        output = ProcessedDataOutput(
            filtro_threshold_minimo=60,
            total_aprovados=3,
            nacional=ScopeContainer(jobs=[job_baixa, job_alta, job_media], post=[]),
            internacional=ScopeContainer(jobs=[], post=[]),
        )

        with TemporaryDirectory() as tmpdir:
            caminho_relatorio = Path(tmpdir) / "relatorio.md"
            gerar_relatorio_markdown(output, caminho_relatorio)

            conteudo = caminho_relatorio.read_text(encoding="utf-8")
            self.assertIn("🔥", conteudo)
            self.assertIn("🚀", conteudo)
            self.assertIn("🎯", conteudo)

            pos_alta = conteudo.find("Python Tech Lead")
            pos_media = conteudo.find("Python Dev Pleno")
            pos_baixa = conteudo.find("Python Dev Jr")

            self.assertTrue(pos_alta < pos_media < pos_baixa)

    def test_job_search_facade_post_processing_ordering(self):
        facade = JobSearchMasterFacade()
        job1 = JobItem(
            job_id="1",
            titulo="Vaga 1",
            descricao_resumida="Desenvolvedor Python Django PostgreSQL REST APIs",
            link="https://linkedin.com/jobs/view/1",
        )
        job2 = JobItem(
            job_id="2",
            titulo="Vaga 2",
            descricao_resumida="Desenvolvedor Python Django FastAPI Docker PostgreSQL Redis AWS Linux Git REST APIs",
            link="https://linkedin.com/jobs/view/2",
        )

        resultado = facade.executar_pos_processamento(
            jobs_nac=[job1, job2],
            jobs_int=[],
            posts_nac=[],
            posts_int=[],
        )

        self.assertEqual(len(resultado.nacional.jobs), 2)
        score_primeiro = resultado.nacional.jobs[0].match_curriculo.score_maximo
        score_segundo = resultado.nacional.jobs[1].match_curriculo.score_maximo
        self.assertGreaterEqual(score_primeiro, score_segundo)



if __name__ == "__main__":
    unittest.main()
