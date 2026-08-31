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


class TimeFilterEnum(StrEnum):
    ULTIMAS_24H = "24h"
    ULTIMA_SEMANA = "semana"
    ULTIMO_MES = "mes"
    QUALQUER_DATA = "tudo"

    @property
    def linkedin_tpr(self) -> str:
        mapping = {
            TimeFilterEnum.ULTIMAS_24H: "r86400",
            TimeFilterEnum.ULTIMA_SEMANA: "r604800",
            TimeFilterEnum.ULTIMO_MES: "r2592000",
            TimeFilterEnum.QUALQUER_DATA: "",
        }
        return mapping.get(self, "r604800")

    @property
    def ddgs_timelimit(self) -> str | None:
        mapping = {
            TimeFilterEnum.ULTIMAS_24H: "d",
            TimeFilterEnum.ULTIMA_SEMANA: "w",
            TimeFilterEnum.ULTIMO_MES: "m",
            TimeFilterEnum.QUALQUER_DATA: None,
        }
        return mapping.get(self, "w")

    @property
    def descricao(self) -> str:
        mapping = {
            TimeFilterEnum.ULTIMAS_24H: "Últimas 24 horas",
            TimeFilterEnum.ULTIMA_SEMANA: "Última semana",
            TimeFilterEnum.ULTIMO_MES: "Último mês",
            TimeFilterEnum.QUALQUER_DATA: "Qualquer data",
        }
        return mapping.get(self, self.value)
