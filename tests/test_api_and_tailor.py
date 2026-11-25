import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.api.main import create_app
from app.api.run_manager import BackgroundRunManager
from app.core.logging import logger as app_logger
from app.core.user_config import UserSearchConfig, add_company_to_blacklist, load_search_config
from app.db import init_db, save_evaluation, upsert_scraped_jobs
from app.models.enums import SeniorityEnum, WorkModelEnum
from app.models.job import JobItem
from app.models.match import LlmEvaluation, MatchLevelEnum, ProfileMatch, ResumeMatch
from app.shared.classifiers import avaliar_pre_filtro_job_bruto
from app.shared.html_formatter import html_to_markdown
from app.tailor.models import (
    ExperienceBullet,
    ExperienceEntry,
    MasterProfile,
    ProfileIdentity,
    SkillGroup,
    TailoredDiff,
)
from app.tailor.parser import _sanitize_nulls
from app.tailor.renderer import render_tailored_resume_pdf
from app.tailor.service import verify_tailored_diff


class TestApiConfigAndTailor(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)
        self.db_path = self.tmp_path / "test.db"
        self.engine = init_db(self.db_path)

        with Session(self.engine) as session:
            item_ok = JobItem(
                job_id="101",
                provider="LinkedIn",
                titulo="Backend Python Developer",
                empresa="Acme Corp",
                localizacao="Remote",
                senioridade=SeniorityEnum.JUNIOR,
                modelo_trabalho=WorkModelEnum.REMOTO,
                link="https://example.com/jobs/101",
                descricao_completa="Looking for Python and FastAPI developer.",
                match_curriculo=ResumeMatch(
                    perfil=ProfileMatch(
                        score_porcentagem=85,
                        nivel=MatchLevelEnum.EXCELENTE,
                        habilidades_compativeis=["Python", "FastAPI"],
                        total_habilidades_encontradas=2,
                    ),
                    avaliacao_llm=LlmEvaluation(
                        aprovado=True,
                        score_llm=88,
                        justificativa="Strong Python/FastAPI fit.",
                        status="APPROVED",
                    ),
                ),
            )
            item_rej = JobItem(
                job_id="102",
                provider="Gupy",
                titulo="Java Senior Engineer",
                empresa="BlockedCo",
                localizacao="São Paulo",
                senioridade=SeniorityEnum.SENIOR,
                modelo_trabalho=WorkModelEnum.PRESENCIAL,
                link="https://example.com/jobs/102",
                descricao_completa="Java 17 required.",
                camada_descarte="Camada 1 - Score de Keywords",
                motivo_descarte="Low keyword match",
            )
            pairs, _ = upsert_scraped_jobs(session, [item_ok, item_rej])
            save_evaluation(session, pairs[0][0], pairs[0][1], llm_status="APPROVED")
            save_evaluation(session, pairs[1][0], pairs[1][1], llm_status="SKIPPED")
            session.commit()
            self.job_ok_id = pairs[0][0].id
            self.job_rej_id = pairs[1][0].id

        self.app = create_app()

        def _override_db():
            with Session(self.engine) as session:
                yield session

        self.app.dependency_overrides[get_db_session] = _override_db
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()
        self.tmp_dir.cleanup()

    def test_dynamic_company_blacklist_in_layer1(self) -> None:
        cfg_path = self.tmp_path / "search_config.json"
        cfg = load_search_config(cfg_path)
        self.assertIsInstance(cfg, UserSearchConfig)

        updated = add_company_to_blacklist("evilcorp", cfg_path)
        self.assertIn("evilcorp", updated.blacklisted_companies)

        approved, reason = avaliar_pre_filtro_job_bruto(
            titulo="Python Developer",
            localizacao="Remote",
            apenas_remoto=True,
            senioridade_filtro="JUNIOR",
            empresa="EvilCorp Labs",
            blacklisted_companies=updated.blacklisted_companies,
        )
        self.assertFalse(approved)
        self.assertIn("Evilcorp", reason or "")

    def test_jobs_list_detail_and_status_transition(self) -> None:
        resp = self.client.get("/api/jobs?status=NEW&min_score=70")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["items"][0]["company"], "Acme Corp")

        detail = self.client.get(f"/api/jobs/{self.job_ok_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertIn("FastAPI", detail.json()["description_md"])

        patch_resp = self.client.patch(
            f"/api/jobs/{self.job_rej_id}/status",
            json={"status": "SAVED", "notes": "Rescued from audit log"},
        )
        self.assertEqual(patch_resp.status_code, 200)
        self.assertEqual(patch_resp.json()["status"], "SAVED")
        self.assertEqual(patch_resp.json()["notes"], "Rescued from audit log")

    def test_blacklist_endpoint_ignores_matching_jobs(self) -> None:
        cfg_path = self.tmp_path / "search_config.json"
        with (
            patch("app.api.routers.config.add_company_to_blacklist") as mock_add,
        ):
            mock_add.return_value = UserSearchConfig(blacklisted_companies=["acme corp"])
            resp = self.client.post(
                "/api/config/blacklist",
                json={"company_name": "Acme Corp", "ignore_existing": True},
            )
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json()["ignored_jobs_count"], 1)

        detail = self.client.get(f"/api/jobs/{self.job_ok_id}")
        self.assertEqual(detail.json()["application"]["status"], "IGNORED")
        self.assertFalse(cfg_path.exists())

    def test_anti_hallucination_verifier_and_1page_pdf(self) -> None:
        profile = MasterProfile(
            identity=ProfileIdentity(
                full_name="Jane Doe",
                headline="Backend Engineer",
                email="jane@example.com",
                location="Remote",
            ),
            default_summary="Backend engineer focused on Python and distributed APIs.",
            experiences=[
                ExperienceEntry(
                    id="exp_acme",
                    company="Acme",
                    role="Software Engineer",
                    start_date="2024",
                    end_date="Present",
                    bullets=[
                        ExperienceBullet(
                            id="exp_acme_1",
                            text="Reduced API latency by 40% using FastAPI and Redis caching.",
                            tags=["python", "fastapi", "redis"],
                        )
                    ],
                )
            ],
            skill_groups=[SkillGroup(category="Backend", skills=["Python", "FastAPI", "Redis"])],
        )

        bad_diff = TailoredDiff(
            language="en",
            headline="Senior Python Engineer",
            tailored_summary="Experienced backend engineer.",
            bullet_overrides={
                "exp_acme_1": "Reduced API latency by 85% using FastAPI and Redis caching.",
                "exp_fake_99": "Invented bullet",
            },
        )
        warnings = verify_tailored_diff(profile, bad_diff)
        warning_types = {warning.warning_type for warning in warnings}
        self.assertIn("new_number", warning_types)
        self.assertIn("unknown_bullet_id", warning_types)

        clean_diff = TailoredDiff(
            language="en",
            headline="Python Backend Engineer",
            tailored_summary="Backend engineer specializing in FastAPI and Redis.",
            bullet_overrides={
                "exp_acme_1": "Cut API latency by 40% with FastAPI and Redis caching.",
            },
        )
        pdf_path, pages, overflow = render_tailored_resume_pdf(
            job_id=999,
            profile=profile,
            diff=clean_diff,
            output_dir=self.tmp_path,
        )
        self.assertTrue(pdf_path.exists())
        self.assertEqual(pages, 1)
        self.assertIsNone(overflow)

    def test_html_to_markdown_and_null_sanitization(self) -> None:
        raw_html = "<h3>Requirements</h3><p>Build <strong>Python</strong> APIs.</p><ul><li>FastAPI</li><li>SQLite</li></ul>"
        formatted = html_to_markdown(raw_html)
        self.assertIn("## Requirements", formatted)
        self.assertIn("**Python**", formatted)
        self.assertIn("- FastAPI", formatted)
        self.assertIn("- SQLite", formatted)

        sanitized = _sanitize_nulls({"phone": None, "location": "Remote", "highlights": [None, "GPA 9.0"]})
        self.assertEqual(sanitized, {"location": "Remote", "highlights": ["GPA 9.0"]})

    def test_run_manager_captures_job_search_logger(self) -> None:
        manager = BackgroundRunManager()

        def _emit_log() -> None:
            app_logger.info("Test SSE log line")

        run_id = manager.start_run("test", _emit_log)
        self.assertIsNotNone(run_id)
        if run_id is not None:
            for _ in range(20):
                if not manager.is_running:
                    break
                time.sleep(0.05)
            sub = manager.subscribe(run_id)
            self.assertIsNotNone(sub)
            if sub is not None:
                snapshot, _, _ = sub
                self.assertTrue(any("Test SSE log line" in line for line in snapshot))
