from typing import Any

from pydantic import BaseModel, Field


class ScoringRule(BaseModel):
    skills: list[str] = Field(..., description="Lista de habilidades analisadas na regra.")
    pontos: int = Field(..., description="Pontuação atribuída se a condição for satisfeita.")
    requer_todos: bool = Field(
        default=False,
        description="Se True, todas as skills devem estar presentes. Se False, basta pelo menos uma.",
    )


class Profile(BaseModel):
    name: str = Field(default="padrao", description="Identificador único do perfil.")
    display_name: str = Field(default="Desenvolvedor Python", description="Nome de exibição amigável do perfil.")
    skills_map: dict[str, str] = Field(
        default_factory=dict,
        description="Dicionário de mapeamento de palavras-chave para o nome canônico da habilidade.",
    )
    primary_skill: str | None = Field(
        default="Python",
        description="Habilidade primária que destrava pontuação máxima no cálculo de compatibilidade.",
    )
    regras_pontuacao: list[ScoringRule] = Field(
        default_factory=list,
        description="Regras de pontuação para cálculo do score do perfil.",
    )
    queries_jobs: list[str] = Field(
        default_factory=list,
        description="Lista única de queries de tecnologias para busca de vagas no LinkedIn.",
    )
    queries_ats: list[str] = Field(
        default_factory=list,
        description="Lista única de termos de busca de vagas na API da Gupy.",
    )
    termos_cargo_inhire: list[str] = Field(
        default_factory=list,
        description="Palavras-chave de título/stack para filtrar vagas nos tenants da InHire.",
    )
    metadados: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadados extras opcionais do perfil.",
    )
