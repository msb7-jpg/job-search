from app.profiles.base import Profile, ScoringRule
from app.profiles.predefined import (
    DEFAULT_PROFILES,
    PROFILE_BACKEND,
    PROFILE_FULLSTACK,
    SKILLS_BACKEND,
    SKILLS_FULLSTACK,
)


def obter_perfil_por_nome(nome: str, perfis: list[Profile]) -> Profile | None:
    for perfil in perfis:
        if perfil.name.lower() == nome.lower():
            return perfil
    return None


__all__ = [
    "DEFAULT_PROFILES",
    "PROFILE_BACKEND",
    "PROFILE_FULLSTACK",
    "SKILLS_BACKEND",
    "SKILLS_FULLSTACK",
    "Profile",
    "ScoringRule",
    "obter_perfil_por_nome",
]
