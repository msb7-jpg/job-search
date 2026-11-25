import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db import (
    compute_canonical_key,
    compute_url_hash,
    get_jobs_for_pdf,
    get_pending_llm_jobs,
    init_db,
    save_evaluation,
    upsert_scraped_jobs,
)
from app.models.enums import MatchLevelEnum, SeniorityEnum, WorkModelEnum
from app.models.job import JobItem
from app.models.match import LlmEvaluation, ProfileMatch, ResumeMatch
from app.pipeline import rejudge_pending_jobs


class TestDbAndDeduplication(unittest.TestCase):
    def test_wal_mode_and_url_hash_dedup(self) -> None:
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            engine = init_db(db_path)

            with engine.connect() as conn:
                mode = conn.execute(text("PRAGMA journal_mode;")).scalar()
                self.assertEqual(str(mode).lower(), "wal")

            # Mesma URL com tracking params diferentes deve gerar mesmo url_hash
            h1 = compute_url_hash("https://example.com/jobs/123/?utm_source=linkedin&trk=abc")
            h2 = compute_url_hash("https://example.com/jobs/123")
            self.assertEqual(h1, h2)

            vaga = JobItem(
                job_id="123",
                provider="LinkedIn",
                titulo="Python Junior Developer",
                empresa="Acme",
                localizacao="Remote",
                senioridade=SeniorityEnum.JUNIOR,
                modelo_trabalho=WorkModelEnum.REMOTO,
                link="https://example.com/jobs/123",
                descricao_completa="Python Django FastAPI",
                match_curriculo=ResumeMatch(
                    perfil=ProfileMatch(score_porcentagem=85, nivel=MatchLevelEnum.EXCELENTE, habilidades_compativeis=["Python"]),
                    avaliacao_llm=LlmEvaluation(aprovado=True, score_llm=90, status="APPROVED", justificativa="OK"),
                ),
            )

            with Session(engine) as session:
                novas, puladas = upsert_scraped_jobs(session, [vaga])
                self.assertEqual(len(novas), 1)
                self.assertEqual(len(puladas), 0)
                save_evaluation(session, novas[0][0], vaga, llm_status="APPROVED")
                session.commit()

                # Segunda execução: mesma vaga não deve ser reavaliada
                novas_2, puladas_2 = upsert_scraped_jobs(session, [vaga])
                self.assertEqual(len(novas_2), 0)
                self.assertEqual(len(puladas_2), 1)
            engine.dispose()

    def test_canonical_key_non_unique_preserves_multi_provider_links(self) -> None:
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            engine = init_db(db_path)

            vaga_linkedin = JobItem(
                job_id="li_1",
                provider="LinkedIn",
                titulo="Backend Python Jr",
                empresa="TechCorp",
                modelo_trabalho=WorkModelEnum.REMOTO,
                link="https://linkedin.com/jobs/view/1",
            )
            vaga_gupy = JobItem(
                job_id="gupy_1",
                provider="Gupy",
                titulo="Backend Python Jr",
                empresa="TechCorp",
                modelo_trabalho=WorkModelEnum.REMOTO,
                link="https://techcorp.gupy.io/jobs/1",
            )
            self.assertEqual(
                compute_canonical_key("TechCorp", "Backend Python Jr", "Remoto"),
                compute_canonical_key("techcorp", "backend python jr", "remoto"),
            )

            with Session(engine) as session:
                novas, _ = upsert_scraped_jobs(session, [vaga_linkedin, vaga_gupy])
                self.assertEqual(len(novas), 2)
                self.assertEqual(novas[0][0].canonical_key, novas[1][0].canonical_key)
                self.assertNotEqual(novas[0][0].url, novas[1][0].url)
            engine.dispose()

    @patch("app.pipeline.export_pdfs_from_db")
    @patch("app.matchers.llm_matcher.verificar_servidor_llm_ativo", return_value=(True, "test-model"))
    @patch(
        "app.matchers.llm_matcher.avaliar_vaga_com_llm",
        return_value=LlmEvaluation(aprovado=True, score_llm=88, status="APPROVED", justificativa="Aprovada no retry"),
    )
    def test_pending_llm_rejudge_recovery(self, _mock_eval, _mock_ping, _mock_pdf) -> None:
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            settings = Settings(database_path=db_path, usar_proxy=False, usar_filtro_llm=True)
            engine = init_db(db_path)

            vaga = JobItem(
                job_id="p_1",
                provider="Gupy",
                titulo="Desenvolvedor Python Junior",
                empresa="Empresa X",
                localizacao="Remoto",
                senioridade=SeniorityEnum.JUNIOR,
                modelo_trabalho=WorkModelEnum.REMOTO,
                link="https://gupy.io/jobs/p_1",
                descricao_completa="Python, Django, FastAPI, PostgreSQL, Docker, Git, Vue.js, React, TypeScript",
            )

            with Session(engine) as session:
                novas, _ = upsert_scraped_jobs(session, [vaga])
                save_evaluation(session, novas[0][0], vaga, llm_status="PENDING")
                session.commit()
                self.assertEqual(len(get_pending_llm_jobs(session)), 1)

            aprovadas, rejeitadas, pendentes = rejudge_pending_jobs(settings=settings)
            self.assertEqual((aprovadas, rejeitadas, pendentes), (1, 0, 0))

            with Session(engine) as session:
                self.assertEqual(len(get_pending_llm_jobs(session)), 0)
                qualificadas, _ = get_jobs_for_pdf(session)
                self.assertEqual(len(qualificadas), 1)
                self.assertEqual(qualificadas[0].job_id, "p_1")
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
