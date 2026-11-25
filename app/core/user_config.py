import json
from pathlib import Path

from pydantic import BaseModel, Field

from app.core.config import DATA_DIR, Settings
from app.profiles.base import Profile, ScoringRule
from app.profiles.predefined import DEFAULT_PROFILE
from app.shared.classifiers import EMPRESAS_BLOQUEADAS

DEFAULT_SEARCH_CONFIG_PATH = DATA_DIR / "search_config.json"


class UserSearchConfig(BaseModel):
    """Configuração dinâmica de busca, pontuação, filtros e blacklist editável pela UI."""

    display_name: str = Field(default=DEFAULT_PROFILE.display_name)
    primary_skill: str | None = Field(default=DEFAULT_PROFILE.primary_skill)
    skills_map: dict[str, str] = Field(default_factory=lambda: dict(DEFAULT_PROFILE.skills_map))
    regras_pontuacao: list[ScoringRule] = Field(default_factory=lambda: [rule.model_copy() for rule in DEFAULT_PROFILE.regras_pontuacao])
    queries_jobs: list[str] = Field(default_factory=lambda: list(DEFAULT_PROFILE.queries_jobs))
    queries_ats: list[str] = Field(default_factory=lambda: list(DEFAULT_PROFILE.queries_ats))
    termos_cargo_inhire: list[str] = Field(default_factory=lambda: list(DEFAULT_PROFILE.termos_cargo_inhire))
    blacklisted_companies: list[str] = Field(default_factory=lambda: list(EMPRESAS_BLOQUEADAS))

    apenas_remoto: bool = Field(default=True)
    senioridade_filtro: str = Field(default="JUNIOR")
    threshold_minimo_match: int = Field(default=60, ge=0, le=100)
    max_anos_experiencia: int = Field(default=2, ge=0, le=20)

    def to_profile(self) -> Profile:
        return Profile(
            name="custom",
            display_name=self.display_name,
            skills_map=self.skills_map,
            primary_skill=self.primary_skill,
            regras_pontuacao=self.regras_pontuacao,
            queries_jobs=self.queries_jobs,
            queries_ats=self.queries_ats,
            termos_cargo_inhire=self.termos_cargo_inhire,
        )

    def apply_to_settings(self, settings: Settings) -> Settings:
        updated = settings.model_copy()
        updated.apenas_remoto = self.apenas_remoto
        updated.senioridade_filtro = self.senioridade_filtro
        updated.threshold_minimo_match = self.threshold_minimo_match
        updated.max_anos_experiencia = self.max_anos_experiencia
        return updated


def load_search_config(config_path: Path = DEFAULT_SEARCH_CONFIG_PATH) -> UserSearchConfig:
    """Carrega a configuração dinâmica do disco ou inicializa com os padrões do projeto."""
    if config_path.exists():
        raw = json.loads(config_path.read_text(encoding="utf-8"))
        return UserSearchConfig.model_validate(raw)

    config = UserSearchConfig()
    save_search_config(config, config_path)
    return config


def save_search_config(config: UserSearchConfig, config_path: Path = DEFAULT_SEARCH_CONFIG_PATH) -> UserSearchConfig:
    """Persiste a configuração dinâmica em JSON formatado."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    normalized = [company.strip().lower() for company in config.blacklisted_companies if company.strip()]
    config.blacklisted_companies = list(dict.fromkeys(normalized))
    config_path.write_text(
        json.dumps(config.model_dump(mode="json"), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return config


def add_company_to_blacklist(company_name: str, config_path: Path = DEFAULT_SEARCH_CONFIG_PATH) -> UserSearchConfig:
    """Adiciona uma empresa à blacklist dinâmica sem duplicatas."""
    config = load_search_config(config_path)
    clean = company_name.strip().lower()
    if clean and clean not in config.blacklisted_companies:
        config.blacklisted_companies.append(clean)
        save_search_config(config, config_path)
    return config
