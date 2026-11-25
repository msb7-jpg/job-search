import json
from pathlib import Path

from pydantic import BaseModel, Field

from app.core.config import DATA_DIR
from app.profiles.base import ScoringRule

DEFAULT_MASTER_PROFILE_PATH = DATA_DIR / "master_profile.json"


class ProfileIdentity(BaseModel):
    full_name: str = ""
    headline: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin_url: str = ""
    github_url: str = ""
    portfolio_url: str = ""


class ExperienceBullet(BaseModel):
    id: str
    text: str
    tags: list[str] = Field(default_factory=list)


class ExperienceEntry(BaseModel):
    id: str
    company: str
    role: str
    location: str = ""
    start_date: str = ""
    end_date: str = "Present"
    bullets: list[ExperienceBullet] = Field(default_factory=list)


class EducationEntry(BaseModel):
    institution: str
    degree: str
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    highlights: list[str] = Field(default_factory=list)


class SkillGroup(BaseModel):
    category: str
    skills: list[str] = Field(default_factory=list)


class LanguageEntry(BaseModel):
    language: str
    proficiency: str


class MasterProfile(BaseModel):
    """Perfil mestre estruturado e editável pela UI (zero dados pessoais hardcoded)."""

    version: str = "v1"
    identity: ProfileIdentity = Field(default_factory=ProfileIdentity)
    default_summary: str = ""
    experiences: list[ExperienceEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    skill_groups: list[SkillGroup] = Field(default_factory=list)
    languages: list[LanguageEntry] = Field(default_factory=list)
    qa_vault: dict[str, str] = Field(
        default_factory=lambda: {
            "salary_expectation_brl": "",
            "salary_expectation_usd": "",
            "notice_period": "",
            "work_authorization": "",
            "english_level": "",
        }
    )

    def to_llm_summary_text(self) -> str:
        """Serializa o perfil em texto conciso para o LLM Judge."""
        parts: list[str] = []
        if self.identity.full_name:
            parts.append(f"Candidato: {self.identity.full_name} ({self.identity.location})")
        if self.default_summary:
            parts.append(f"Resumo: {self.default_summary}")
        for exp in self.experiences:
            bullets_txt = "; ".join(bullet.text for bullet in exp.bullets[:4])
            parts.append(f"- {exp.role} @ {exp.company} ({exp.start_date} - {exp.end_date}): {bullets_txt}")
        if self.skill_groups:
            skills_txt = " | ".join(f"{group.category}: {', '.join(group.skills)}" for group in self.skill_groups)
            parts.append(f"Stack: {skills_txt}")
        if self.languages:
            langs_txt = ", ".join(f"{lang.language} ({lang.proficiency})" for lang in self.languages)
            parts.append(f"Idiomas: {langs_txt}")
        return "\n".join(parts)[:3500]


class ParsedResumeResult(BaseModel):
    """Resultado do parser LLM de currículo: perfil estruturado + queries/skills sugeridas."""

    profile: MasterProfile
    suggested_primary_skill: str | None = None
    suggested_skills_map: dict[str, str] = Field(default_factory=dict)
    suggested_scoring_rules: list[ScoringRule] = Field(default_factory=list)
    suggested_queries_jobs: list[str] = Field(default_factory=list)
    suggested_queries_ats: list[str] = Field(default_factory=list)
    suggested_inhire_terms: list[str] = Field(default_factory=list)


class TailoredDiff(BaseModel):
    """Saída estruturada e restrita do LLM para adaptação de currículo sem alucinações."""

    language: str = "en"
    headline: str = ""
    tailored_summary: str = ""
    selected_skill_groups: list[SkillGroup] = Field(default_factory=list)
    bullet_overrides: dict[str, str] = Field(default_factory=dict)
    cover_letter_md: str = ""
    missing_keywords_honest_note: list[str] = Field(default_factory=list)


class VerificationWarning(BaseModel):
    bullet_id: str
    warning_type: str
    details: str
    original_text: str = ""
    tailored_text: str = ""


def load_master_profile(path: Path = DEFAULT_MASTER_PROFILE_PATH) -> MasterProfile:
    if path.exists():
        raw = json.loads(path.read_text(encoding="utf-8"))
        return MasterProfile.model_validate(raw)
    return MasterProfile()


def save_master_profile(profile: MasterProfile, path: Path = DEFAULT_MASTER_PROFILE_PATH) -> MasterProfile:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(profile.model_dump(mode="json"), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return profile
