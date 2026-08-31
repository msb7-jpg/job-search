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
    name: str = Field(..., description="Identificador único em minúsculas (ex: 'backend', 'fullstack').")
    display_name: str = Field(..., description="Nome de exibição amigável do perfil.")
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
    queries_jobs_nacionais: list[tuple[str, str]] = Field(
        default_factory=list,
        description="Lista de tuplas (palavra-chave, localização) para busca de vagas nacionais.",
    )
    queries_jobs_internacionais: list[tuple[str, str]] = Field(
        default_factory=list,
        description="Lista de tuplas (query, localização) para busca de vagas internacionais.",
    )
    queries_posts_nacionais: list[str] = Field(
        default_factory=list,
        description="Lista de queries booleanas para busca de posts nacionais via SearXNG.",
    )
    queries_posts_internacionais: list[str] = Field(
        default_factory=list,
        description="Lista de queries booleanas para busca de posts internacionais via SearXNG.",
    )
    metadados: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadados extras opcionais do perfil.",
    )
