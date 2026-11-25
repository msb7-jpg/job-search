import io
import json
import re

import requests
from pydantic import ValidationError
from pypdf import PdfReader

from app.core.config import Settings, settings as default_settings
from app.matchers.llm_matcher import _extrair_json_resposta, _montar_headers_llm
from app.tailor.models import MasterProfile, ParsedResumeResult


class ResumeParseError(RuntimeError):
    @classmethod
    def empty_text(cls) -> "ResumeParseError":
        return cls("Texto do currículo vazio.")

    @classmethod
    def llm_failed(cls, exc: Exception) -> "ResumeParseError":
        return cls(f"Falha ao consultar LLM para parse do currículo: {exc}")

    @classmethod
    def invalid_json(cls, details: str = "") -> "ResumeParseError":
        suffix = f" ({details})" if details else ""
        return cls(f"O LLM não retornou um JSON válido para o perfil.{suffix}")


def _sanitize_nulls(value: object) -> object:
    """Converte valores None em strings vazias ou listas para tolerar campos nulos do LLM."""
    if isinstance(value, dict):
        return {key: _sanitize_nulls(val) for key, val in value.items() if val is not None}
    if isinstance(value, list):
        return [_sanitize_nulls(item) for item in value if item is not None]
    return value


def extract_text_from_upload(filename: str, content_bytes: bytes) -> str:
    """Extrai texto de arquivos PDF, Markdown ou TXT enviados pela UI."""
    lower = (filename or "").lower()
    if lower.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(content_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()
    return content_bytes.decode("utf-8", errors="replace").strip()


def _slugify(value: str) -> str:
    clean = re.sub(r"[^a-z0-9]+", "_", (value or "").lower()).strip("_")
    return clean[:24] or "item"


def parse_resume_with_llm(
    resume_text: str,
    settings: Settings = default_settings,
) -> ParsedResumeResult:
    """Usa o endpoint OpenAI-compatible para estruturar qualquer currículo em MasterProfile + queries/skills."""
    cleaned = (resume_text or "").strip()
    if not cleaned:
        raise ResumeParseError.empty_text()

    system_prompt = (
        "You are an expert technical recruiter and resume parser. "
        "Convert the user's raw resume text into a strict JSON object matching this exact schema:\n"
        "{\n"
        '  "profile": {\n'
        '    "version": "v1",\n'
        '    "identity": {\n'
        '      "full_name": "...", "headline": "...", "email": "...", "phone": "...",\n'
        '      "location": "...", "linkedin_url": "...", "github_url": "...", "portfolio_url": "..."\n'
        "    },\n"
        '    "default_summary": "2-3 sentence professional summary",\n'
        '    "experiences": [\n'
        "      {\n"
        '        "id": "exp_company_slug",\n'
        '        "company": "...", "role": "...", "location": "...", "start_date": "...", "end_date": "...",\n'
        '        "bullets": [{"id": "exp_company_1", "text": "exact achievement bullet", "tags": ["python", "docker"]}]\n'
        "      }\n"
        "    ],\n"
        '    "education": [{"institution": "...", "degree": "...", "location": "...", "start_date": "...", "end_date": "...", "highlights": ["..."]}],\n'
        '    "skill_groups": [{"category": "Backend", "skills": ["Python", "FastAPI"]}],\n'
        '    "languages": [{"language": "English", "proficiency": "Fluent"}],\n'
        '    "qa_vault": {"salary_expectation_brl": "", "salary_expectation_usd": "", "notice_period": "", "work_authorization": "", "english_level": ""}\n'
        "  },\n"
        '  "suggested_primary_skill": "Python",\n'
        '  "suggested_skills_map": {"python": "Python", "fastapi": "FastAPI"},\n'
        '  "suggested_scoring_rules": [\n'
        '    {"skills": ["Python"], "pontos": 30, "requer_todos": false},\n'
        '    {"skills": ["Django", "FastAPI"], "pontos": 25, "requer_todos": false}\n'
        "  ],\n"
        '  "suggested_queries_jobs": ["Python", "Python FastAPI", "Backend Python"],\n'
        '  "suggested_queries_ats": ["Python", "FastAPI", "PostgreSQL"],\n'
        '  "suggested_inhire_terms": ["python", "backend", "software engineer"]\n'
        "}\n"
        "Rules:\n"
        "- Preserve ALL factual dates, companies, metrics, and achievements from the resume without inventing anything.\n"
        "- Assign unique deterministic bullet IDs like exp_<company>_1, exp_<company>_2.\n"
        "- Suggested scoring rules should total roughly 100 points across the candidate's core stack.\n"
        "- Return ONLY valid JSON."
    )

    payload = {
        "model": settings.llm_model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"=== RAW RESUME ===\n{cleaned[:9000]}"},
        ],
        "temperature": 0.1,
    }

    url = f"{settings.llm_base_url.rstrip('/')}/chat/completions"
    try:
        resp = requests.post(
            url,
            headers=_montar_headers_llm(settings.llm_api_key),
            json=payload,
            timeout=max(settings.llm_timeout, 60),
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        raise ResumeParseError.llm_failed(exc) from exc

    parsed_dict = _extrair_json_resposta(content)
    if not parsed_dict or "profile" not in parsed_dict:
        raise ResumeParseError.invalid_json()

    try:
        sanitized = _sanitize_nulls(parsed_dict)
        result = ParsedResumeResult.model_validate(sanitized)
    except ValidationError as exc:
        raise ResumeParseError.invalid_json(str(exc.errors()[0].get("msg", ""))) from exc

    # Garante IDs únicos e estáveis caso o LLM omita ou duplique
    seen_ids: set[str] = set()
    for exp_idx, exp in enumerate(result.profile.experiences, start=1):
        if not exp.id:
            exp.id = f"exp_{_slugify(exp.company)}_{exp_idx}"
        for b_idx, bullet in enumerate(exp.bullets, start=1):
            candidate_id = bullet.id or f"{exp.id}_{b_idx}"
            while candidate_id in seen_ids:
                candidate_id = f"{candidate_id}_{b_idx}"
            bullet.id = candidate_id
            seen_ids.add(candidate_id)

    return result


def build_profile_summary_for_judge(profile: MasterProfile) -> str:
    """Retorna texto pronto para o LLM Judge se o perfil estiver preenchido."""
    return profile.to_llm_summary_text()


def dump_parsed_preview(result: ParsedResumeResult) -> str:
    return json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False)
