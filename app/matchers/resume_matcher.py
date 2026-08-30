import re
from typing import Literal

from app.matchers.skills_definitions import SKILLS_BACKEND, SKILLS_FULLSTACK
from app.models.enums import MatchLevelEnum
from app.models.job import JobItem
from app.models.match import ProfileMatch, ResumeMatch
from app.models.post import PostItem


def calcular_nivel_match(score: int) -> MatchLevelEnum:
    if score >= 80:
        return MatchLevelEnum.EXCELENTE
    if score >= 60:
        return MatchLevelEnum.ALTO
    if score >= 40:
        return MatchLevelEnum.MEDIO
    return MatchLevelEnum.BAIXO

def calcular_perfil_match(texto: str, skills_dict: dict[str, str], foco: Literal["backend", "fullstack"]) -> ProfileMatch:
    texto_lower = texto.lower()
    habilidades_encontradas: set[str] = set()

    for kw, skill_name in skills_dict.items():
        pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, texto_lower):
            habilidades_encontradas.add(skill_name)

    habilidades_lista = sorted(habilidades_encontradas)
    pontos = 0

    if "Python" in habilidades_encontradas:
        pontos += 25
    if "Django" in habilidades_encontradas or "FastAPI" in habilidades_encontradas:
        pontos += 20
    if "PostgreSQL" in habilidades_encontradas or "MySQL" in habilidades_encontradas or "SQL" in habilidades_encontradas:
        pontos += 15
    if "Docker" in habilidades_encontradas or "AWS" in habilidades_encontradas or "GCP" in habilidades_encontradas or "Linux" in habilidades_encontradas:
        pontos += 15
    if "REST APIs" in habilidades_encontradas or "Pytest" in habilidades_encontradas or "Git" in habilidades_encontradas:
        pontos += 10

    if (foco == "fullstack" and (
        "Vue.js" in habilidades_encontradas or
        "React.js" in habilidades_encontradas or
        "TypeScript" in habilidades_encontradas or
        "JavaScript" in habilidades_encontradas
    )) or (
        foco == "backend" and (
            "Redis" in habilidades_encontradas or
            "RabbitMQ" in habilidades_encontradas or
            "Celery" in habilidades_encontradas or
            "Microservices" in habilidades_encontradas
        )
    ):
        pontos += 15

    score_final = min(100, max(15, pontos)) if "Python" in habilidades_encontradas else min(50, pontos)

    return ProfileMatch(
        score_porcentagem=score_final,
        nivel=calcular_nivel_match(score_final),
        habilidades_compativeis=habilidades_lista,
        total_habilidades_encontradas=len(habilidades_lista),
    )

def avaliar_compatibilidade(item: JobItem | PostItem) -> ResumeMatch:
    texto = f"{item.titulo} {item.descricao_completa or item.descricao_resumida}"
    match_be = calcular_perfil_match(texto, SKILLS_BACKEND, foco="backend")
    match_fs = calcular_perfil_match(texto, SKILLS_FULLSTACK, foco="fullstack")
    return ResumeMatch(backend=match_be, fullstack=match_fs)
