from pydantic import BaseModel

from app.models.enums import SeniorityEnum, WorkModelEnum
from app.models.match import ResumeMatch


class JobItem(BaseModel):
    job_id: str
    provider: str = "LinkedIn"
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
