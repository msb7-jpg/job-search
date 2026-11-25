from pydantic import BaseModel, Field

from app.models.enums import MatchLevelEnum


class ProfileMatch(BaseModel):
    nome_perfil: str = "padrao"
    score_porcentagem: int = Field(..., ge=0, le=100)
    nivel: MatchLevelEnum
    habilidades_compativeis: list[str] = Field(default_factory=list)
    total_habilidades_encontradas: int = 0


class LlmEvaluation(BaseModel):
    aprovado: bool = Field(
        default=False,
        description="True apenas se for Júnior (<=2 anos XP), 100% Remota viável do Brasil e compatível com a stack.",
    )
    score_llm: int = Field(default=0, ge=0, le=100)
    nivel_detectado: str = Field(default="Não Identificado")
    anos_experiencia_exigidos: int | None = Field(default=None)
    remoto_viavel_brasil: bool = Field(default=True)
    justificativa: str = Field(default="")
    status: str = Field(default="PENDING")


class ResumeMatch(BaseModel):
    perfil: ProfileMatch | None = None
    avaliacao_llm: LlmEvaluation | None = None

    @property
    def score_maximo(self) -> int:
        return self.perfil.score_porcentagem if self.perfil else 0

    @property
    def total_skills_maximo(self) -> int:
        return len(self.perfil.habilidades_compativeis) if self.perfil else 0
