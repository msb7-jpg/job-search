from pydantic import BaseModel, Field

from app.models.enums import MatchLevelEnum


class ProfileMatch(BaseModel):
    score_porcentagem: int = Field(..., ge=0, le=100)
    nivel: MatchLevelEnum
    habilidades_compativeis: list[str] = Field(default_factory=list)
    total_habilidades_encontradas: int = 0

class ResumeMatch(BaseModel):
    backend: ProfileMatch
    fullstack: ProfileMatch
