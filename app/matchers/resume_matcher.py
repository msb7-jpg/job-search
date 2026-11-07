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

    tem_habilidade_primaria = perfil.primary_skill in habilidades_encontradas if perfil.primary_skill is not None else True

    score_calculado = min(100, max(15, pontos_acumulados)) if tem_habilidade_primaria else min(50, pontos_acumulados)

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


TECNOLOGIAS_CONCORRENTES_MAP: dict[str, str] = {
    r"\bjava\b": "Java",
    r"\bspring(?:-boot)?\b": "Spring Boot",
    r"\bc#\b|\bcsharp\b": "C#",
    r"\b\.net\b|\bdotnet\b": ".NET",
    r"\bphp\b": "PHP",
    r"\blaravel\b": "Laravel",
    r"\bruby\b": "Ruby",
    r"\brails\b|\bruby on rails\b": "Ruby on Rails",
    r"\bangular\b": "Angular",
    r"\bgolang\b": "Go",
    r"\bswift\b": "Swift",
    r"\bkotlin\b": "Kotlin",
    r"\bflutter\b": "Flutter",
    r"\bsap\b": "SAP",
    r"\bsalesforce\b": "Salesforce",
    r"\bc\+\+\b": "C++",
    r"\brust\b": "Rust",
    r"\bscala\b": "Scala",
}


def gerar_diagnostico_descarte_keywords(
    item: JobItem | PostItem,
    match_curriculo: ResumeMatch | None,
    threshold: int,
) -> str:
    texto_analise = f"{item.titulo} {item.descricao_completa or item.descricao_resumida}".lower()

    # 1. Habilidades compatíveis encontradas
    habilidades_encontradas: set[str] = set()
    if match_curriculo and match_curriculo.perfis:
        for perfil_match in match_curriculo.perfis.values():
            habilidades_encontradas.update(perfil_match.habilidades_compativeis)

    score_max = match_curriculo.score_maximo if match_curriculo else 0

    # 2. Tecnologias essenciais do perfil do candidato que faltavam na vaga
    faltando_essenciais: list[str] = []
    if "Python" not in habilidades_encontradas:
        faltando_essenciais.append("Python (Linguagem Principal)")
    if not any(fw in habilidades_encontradas for fw in ["Django", "FastAPI", "Flask"]):
        faltando_essenciais.append("Framework Backend (Django/FastAPI/Flask)")
    if not any(fw in habilidades_encontradas for fw in ["Vue.js", "React.js", "TypeScript"]):
        faltando_essenciais.append("Frontend Moderno (Vue.js/React.js/TypeScript)")

    # 3. Tecnologias concorrentes / outras stacks identificadas no texto da vaga
    concorrentes_detectadas: set[str] = set()
    for padrao, nome_tech in TECNOLOGIAS_CONCORRENTES_MAP.items():
        if re.search(padrao, texto_analise):
            concorrentes_detectadas.add(nome_tech)

    partes: list[str] = [f"Compatibilidade insuficiente com o currículo (Score máximo: {score_max}% < {threshold}%)."]

    if habilidades_encontradas:
        partes.append(f"Tecnologias compatíveis identificadas: {', '.join(sorted(habilidades_encontradas))}.")
    else:
        partes.append("Nenhuma tecnologia compatível com seu perfil foi identificada na descrição.")

    if faltando_essenciais:
        partes.append(f"Tecnologias essenciais ausentes na vaga: {', '.join(faltando_essenciais)}.")

    if concorrentes_detectadas:
        partes.append(f"Foco técnico da vaga identificado em outra stack: {', '.join(sorted(concorrentes_detectadas))}.")

    return " ".join(partes)
