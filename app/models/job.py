from pydantic import BaseModel

from app.models.enums import ItemTypeEnum, PlatformEnum, ScopeEnum, SeniorityEnum, WorkModelEnum
from app.models.match import ResumeMatch


class JobItem(BaseModel):
    job_id: str
    tipo: ItemTypeEnum = ItemTypeEnum.JOB
    plataforma: PlatformEnum = PlatformEnum.LINKEDIN
    escopo: ScopeEnum = ScopeEnum.NACIONAL
    titulo: str
    empresa: str = "N/A"
    localizacao: str = "Brazil"
    data_postagem: str = "Recente"
    senioridade: SeniorityEnum = SeniorityEnum.NAO_ESPECIFICADO
    modelo_trabalho: WorkModelEnum = WorkModelEnum.NAO_ESPECIFICADO
    link: str
    descricao_resumida: str = ""
    descricao_completa: str = ""
    match_curriculo: ResumeMatch | None = None
    motivo_descarte: str | None = None
    camada_descarte: str | None = None
