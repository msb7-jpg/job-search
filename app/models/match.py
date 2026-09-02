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

    @property
    def score_maximo(self) -> int:
        if self.perfis:
            return max((perfil.score_porcentagem for perfil in self.perfis.values()), default=0)
        scores = []
        if self.backend:
            scores.append(self.backend.score_porcentagem)
        if self.fullstack:
            scores.append(self.fullstack.score_porcentagem)
        return max(scores, default=0)

    @property
    def total_skills_maximo(self) -> int:
        if self.perfis:
            return max((len(perfil.habilidades_compativeis) for perfil in self.perfis.values()), default=0)
        contagens = []
        if self.backend:
            contagens.append(len(self.backend.habilidades_compativeis))
        if self.fullstack:
            contagens.append(len(self.fullstack.habilidades_compativeis))
        return max(contagens, default=0)

