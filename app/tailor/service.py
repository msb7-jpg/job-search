import re

import requests

from app.core.config import Settings, settings as default_settings
from app.matchers.llm_matcher import _extrair_json_resposta, _montar_headers_llm
from app.tailor.models import MasterProfile, TailoredDiff, VerificationWarning

_NUMBER_RE = re.compile(r"\b\d+(?:[.,]\d+)?%?\b")

_PT_STOPWORDS = frozenset(
    {
        "vaga",
        "requisitos",
        "experiência",
        "desenvolvimento",
        "conhecimento",
        "empresa",
        "trabalho",
        "remoto",
        "híbrido",
        "benefícios",
        "candidato",
        "atuação",
        "com",
        "para",
        "como",
    }
)


class TailorGenerationError(RuntimeError):
    @classmethod
    def empty_profile(cls) -> "TailorGenerationError":
        return cls("MasterProfile está vazio. Faça o parse ou preencha seu perfil primeiro.")

    @classmethod
    def llm_failed(cls, exc: Exception) -> "TailorGenerationError":
        return cls(f"Erro ao chamar LLM para tailoring: {exc}")

    @classmethod
    def invalid_json(cls) -> "TailorGenerationError":
        return cls("O LLM não retornou JSON válido para o TailoredDiff.")


def detect_jd_language(text: str) -> str:
    """Detecta de forma determinística se a JD está majoritariamente em português ou inglês."""
    words = re.findall(r"[a-záéíóúâêôãõç]+", (text or "").lower())
    pt_hits = sum(1 for word in words if word in _PT_STOPWORDS)
    return "pt" if pt_hits >= 3 else "en"


def verify_tailored_diff(profile: MasterProfile, diff: TailoredDiff) -> list[VerificationWarning]:
    """Checagem determinística anti-alucinação: sinaliza IDs inexistentes e novos números/porcentagens."""
    original_bullets: dict[str, str] = {}
    for exp in profile.experiences:
        for bullet in exp.bullets:
            original_bullets[bullet.id] = bullet.text

    warnings: list[VerificationWarning] = []
    for bullet_id, tailored_text in diff.bullet_overrides.items():
        if bullet_id not in original_bullets:
            warnings.append(
                VerificationWarning(
                    bullet_id=bullet_id,
                    warning_type="unknown_bullet_id",
                    details=f"Bullet ID '{bullet_id}' não existe no MasterProfile.",
                    original_text="",
                    tailored_text=tailored_text,
                )
            )
            continue

        orig_text = original_bullets[bullet_id]
        orig_nums = set(_NUMBER_RE.findall(orig_text))
        new_nums = set(_NUMBER_RE.findall(tailored_text)) - orig_nums
        if new_nums:
            warnings.append(
                VerificationWarning(
                    bullet_id=bullet_id,
                    warning_type="new_number",
                    details=f"Novos números/métricas introduzidos pela IA: {', '.join(sorted(new_nums))}",
                    original_text=orig_text,
                    tailored_text=tailored_text,
                )
            )

    return warnings


def generate_tailored_diff(
    profile: MasterProfile,
    job_title: str,
    company: str,
    description_md: str,
    include_cover_letter: bool = False,
    settings: Settings = default_settings,
) -> tuple[TailoredDiff, list[VerificationWarning]]:
    """Gera um TailoredDiff estruturado via LLM respeitando estritamente os IDs do MasterProfile."""
    if not profile.experiences and not profile.default_summary:
        raise TailorGenerationError.empty_profile()

    lang = detect_jd_language(f"{job_title}\n{description_md}")
    lang_label = "Portuguese (pt-BR)" if lang == "pt" else "English"

    bullet_catalog = [
        {
            "company": exp.company,
            "role": exp.role,
            "bullets": [{"id": bullet.id, "text": bullet.text, "tags": bullet.tags} for bullet in exp.bullets],
        }
        for exp in profile.experiences
    ]

    skill_catalog = [{"category": group.category, "skills": group.skills} for group in profile.skill_groups]

    system_prompt = (
        "You are an honest, precision resume tailoring assistant.\n"
        f"Target output language: {lang_label}.\n"
        "You MUST return ONLY a valid JSON object matching this exact schema:\n"
        "{\n"
        f'  "language": "{lang}",\n'
        '  "headline": "concise role title aligned to JD",\n'
        '  "tailored_summary": "2-3 sentence summary aligned to JD using ONLY real facts from the profile",\n'
        '  "selected_skill_groups": [{"category": "...", "skills": ["..."]}],\n'
        '  "bullet_overrides": {"<existing_bullet_id>": "rephrased bullet mirroring JD terminology without inventing metrics"},\n'
        f'  "cover_letter_md": "{"concise 3-paragraph cover letter" if include_cover_letter else ""}",\n'
        '  "missing_keywords_honest_note": ["skills requested by JD that the candidate does NOT have"]\n'
        "}\n\n"
        "STRICT ANTI-HALLUCINATION RULES:\n"
        "1. NEVER invent companies, dates, degrees, or numeric metrics.\n"
        "2. In bullet_overrides, ONLY use exact bullet IDs provided in the catalog. Select the most relevant 3-5 bullets per role to fit 1 page.\n"
        "3. In selected_skill_groups, ONLY include skills the candidate actually has, reordered to prioritize JD matches.\n"
        "4. Put any JD requirement the candidate lacks into missing_keywords_honest_note (never fake it)."
    )

    user_prompt = (
        f"=== TARGET JOB ===\nTitle: {job_title}\nCompany: {company}\nDescription:\n{description_md[:4500]}\n\n"
        f"=== CANDIDATE PROFILE ===\nDefault Summary: {profile.default_summary}\n"
        f"Experiences Catalog: {bullet_catalog}\n"
        f"Skills Catalog: {skill_catalog}"
    )

    url = f"{settings.llm_base_url.rstrip('/')}/chat/completions"
    try:
        resp = requests.post(
            url,
            headers=_montar_headers_llm(settings.llm_api_key),
            json={
                "model": settings.llm_model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
            },
            timeout=max(settings.llm_timeout, 60),
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        raise TailorGenerationError.llm_failed(exc) from exc

    parsed = _extrair_json_resposta(content)
    if not parsed:
        raise TailorGenerationError.invalid_json()

    diff = TailoredDiff.model_validate(parsed)
    diff.language = lang
    warnings = verify_tailored_diff(profile, diff)
    return diff, warnings
