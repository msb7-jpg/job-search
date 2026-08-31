from pydantic import BaseModel, Field

from app.models.enums import MatchLevelEnum


class ProfileMatch(BaseModel):
    nome_perfil: str = "default"
    score_porcentagem: int = Field(..., ge=0, le=100)
    nivel: MatchLevelEnum
    habilidades_compativeis: list[str] = Field(default_factory=list)
    total_habilidades_encontradas: int = 0


class ResumeMatch(BaseModel):
    perfis: dict[str, ProfileMatch] = Field(default_factory=dict)
    backend: ProfileMatch | None = None
    fullstack: ProfileMatch | None = None
