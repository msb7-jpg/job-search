from enum import StrEnum


class ScopeEnum(StrEnum):
    NACIONAL = "nacional"
    INTERNACIONAL = "internacional"

class ItemTypeEnum(StrEnum):
    JOB = "jobs"
    POST = "post"

class SeniorityEnum(StrEnum):
    ESTAGIO = "Estágio"
    JUNIOR = "Júnior"
    PLENO = "Pleno"
    SENIOR = "Sênior"
    NAO_ESPECIFICADO = "Não Especificado"

class WorkModelEnum(StrEnum):
    REMOTO = "Remoto"
    PRESENCIAL = "Presencial"
    HIBRIDO = "Híbrido"
    NAO_ESPECIFICADO = "Não Especificado"

class MatchLevelEnum(StrEnum):
    EXCELENTE = "Excelente"
    ALTO = "Alto"
    MEDIO = "Médio"
    BAIXO = "Baixo"
