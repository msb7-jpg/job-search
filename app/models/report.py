from pydantic import BaseModel, Field

from app.models.job import JobItem
from app.models.post import PostItem


class ScopeContainer(BaseModel):
    jobs: list[JobItem] = Field(default_factory=list)
    post: list[PostItem] = Field(default_factory=list)


class ProcessedDataOutput(BaseModel):
    filtro_threshold_minimo: int = 60
    total_aprovados: int = 0
    total_rejeitados: int = 0
    nacional: ScopeContainer = Field(default_factory=ScopeContainer)
    internacional: ScopeContainer = Field(default_factory=ScopeContainer)
    rejeitadas: list[JobItem] = Field(default_factory=list)


class AtsReportOutput(BaseModel):
    filtro_threshold_minimo: int = 60
    total_aprovados: int = 0
    total_gupy: int = 0
    total_inhire: int = 0
    total_rejeitados: int = 0
    vagas: list[JobItem] = Field(default_factory=list)
    vagas_gupy: list[JobItem] = Field(default_factory=list)
    vagas_inhire: list[JobItem] = Field(default_factory=list)
    rejeitadas: list[JobItem] = Field(default_factory=list)
