from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import ItemTypeEnum, ScopeEnum, SeniorityEnum, WorkModelEnum
from app.models.match import ResumeMatch


class PostItem(BaseModel):
    job_id: str
    tipo: ItemTypeEnum = ItemTypeEnum.POST
    escopo: ScopeEnum = ScopeEnum.NACIONAL
    titulo: str = "Post no LinkedIn"
    empresa: str = "LinkedIn Post"
    localizacao: str = "Brasil"
    data_postagem: str = "Recente"
    senioridade: SeniorityEnum = SeniorityEnum.JUNIOR
    modelo_trabalho: WorkModelEnum = WorkModelEnum.REMOTO
    link: str
    descricao_resumida: str = ""
    descricao_completa: str = ""
    raw: dict[str, Any] = Field(default_factory=dict)
    match_curriculo: ResumeMatch | None = None
