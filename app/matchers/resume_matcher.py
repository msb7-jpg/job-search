import re

from app.models.enums import MatchLevelEnum
from app.models.job import JobItem
from app.models.match import ProfileMatch, ResumeMatch
from app.models.post import PostItem
from app.profiles.base import Profile


def calcular_nivel_match(score: int) -> MatchLevelEnum:
    if score >= 80:
        return MatchLevelEnum.EXCELENTE
    if score >= 60:
        return MatchLevelEnum.ALTO
    if score >= 40:
        return MatchLevelEnum.MEDIO
    return MatchLevelEnum.BAIXO


def calcular_perfil_match(texto: str, perfil: Profile) -> ProfileMatch:
    texto_lower = texto.lower()
    habilidades_encontradas: set[str] = set()

    for keyword, nome_habilidade in perfil.skills_map.items():
        padrao_regex = r"\b" + re.escape(keyword) + r"\b"
        if re.search(padrao_regex, texto_lower):
            habilidades_encontradas.add(nome_habilidade)

    habilidades_lista = sorted(habilidades_encontradas)
    pontos_acumulados = 0

    for regra in perfil.regras_pontuacao:
        if regra.requer_todos:
            if all(habilidade in habilidades_encontradas for habilidade in regra.skills):
                pontos_acumulados += regra.pontos
        elif any(habilidade in habilidades_encontradas for habilidade in regra.skills):
            pontos_acumulados += regra.pontos

    tem_habilidade_primaria = (
        perfil.primary_skill in habilidades_encontradas
        if perfil.primary_skill is not None
        else True
    )

    score_calculado = (
        min(100, max(15, pontos_acumulados))
        if tem_habilidade_primaria
        else min(50, pontos_acumulados)
    )

    return ProfileMatch(
        nome_perfil=perfil.name,
        score_porcentagem=score_calculado,
        nivel=calcular_nivel_match(score_calculado),
        habilidades_compativeis=habilidades_lista,
        total_habilidades_encontradas=len(habilidades_lista),
    )


def avaliar_compatibilidade(
    item: JobItem | PostItem,
    perfis: list[Profile],
) -> ResumeMatch:
    texto_analise = f"{item.titulo} {item.descricao_completa or item.descricao_resumida}"

    resultado_perfis: dict[str, ProfileMatch] = {}
    for perfil in perfis:
        resultado_perfis[perfil.name] = calcular_perfil_match(texto_analise, perfil)

    backend_match = resultado_perfis.get("backend")
    fullstack_match = resultado_perfis.get("fullstack")

    return ResumeMatch(
        perfis=resultado_perfis,
        backend=backend_match,
        fullstack=fullstack_match,
    )
