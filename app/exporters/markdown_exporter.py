from pathlib import Path

from app.core.logging import logger
from app.models.match import ResumeMatch
from app.models.report import ProcessedDataOutput


def obter_icone_match(score: int) -> str:
    """Retorna um emoji motivacional com base na pontuação de compatibilidade do currículo."""
    if score >= 90:
        return "🔥"  # Match Perfeito / Top Match (90-100%)
    if score >= 80:
        return "🚀"  # Match Excelente (80-89%)
    if score >= 70:
        return "⚡"  # Match Alto (70-79%)
    if score >= 60:
        return "🎯"  # Match Qualificado (60-69%)
    if score >= 40:
        return "💡"  # Match Médio (40-59%)
    return "⚪"      # Match Baixo (<40%)


def _obter_chave_ordenacao(item: object) -> tuple[int, int]:
    match_curriculo = getattr(item, "match_curriculo", None)
    if not match_curriculo:
        return (0, 0)
    return (
        match_curriculo.score_maximo,
        match_curriculo.total_skills_maximo,
    )


def _formatar_item_markdown(
    indice: int,
    item: object,
    titulo: str,
    empresa: str,
    localizacao: str,
    data_postagem: str,
    link: str,
    match_curriculo: ResumeMatch | None,
) -> list[str]:
    melhor_score = match_curriculo.score_maximo if match_curriculo else 0
    icone_maximo = obter_icone_match(melhor_score)

    perfis_compativeis: list[str] = []
    skills_linhas: list[str] = []

    if match_curriculo and match_curriculo.perfis:
        for profile_name, profile_match in match_curriculo.perfis.items():
            nome_exibicao = profile_name.capitalize()
            icone_perfil = obter_icone_match(profile_match.score_porcentagem)
            if profile_match.score_porcentagem >= 60:
                perfis_compativeis.append(
                    f"{icone_perfil} {nome_exibicao}: {profile_match.score_porcentagem}% ({profile_match.nivel.value})"
                )
            skills_str = (
                ", ".join(profile_match.habilidades_compativeis)
                if profile_match.habilidades_compativeis
                else "N/A"
            )
            skills_linhas.append(f"- **Skills {nome_exibicao}**: `{skills_str}`")
    elif match_curriculo:
        backend_match = match_curriculo.backend
        fullstack_match = match_curriculo.fullstack
        if backend_match and backend_match.score_porcentagem >= 60:
            icone_backend = obter_icone_match(backend_match.score_porcentagem)
            perfis_compativeis.append(
                f"{icone_backend} Backend: {backend_match.score_porcentagem}% ({backend_match.nivel.value})"
            )
        if fullstack_match and fullstack_match.score_porcentagem >= 60:
            icone_fs = obter_icone_match(fullstack_match.score_porcentagem)
            perfis_compativeis.append(
                f"{icone_fs} Full-Stack: {fullstack_match.score_porcentagem}% ({fullstack_match.nivel.value})"
            )

    compatibilidade_str = (
        " | ".join(perfis_compativeis)
        if perfis_compativeis
        else "Sem match mínimo para este currículo"
    )

    linhas = [
        f"### {indice}. {icone_maximo} {titulo} - **Match Máximo: {melhor_score}%**",
        f"- **Compatibilidade**: {compatibilidade_str}",
        f"- **Empresa/Autor**: {empresa} | **Local**: {localizacao} | **Postagem**: {data_postagem}",
    ]
    linhas.extend(skills_linhas)
    linhas.append(f"- 🔗 [Ver no LinkedIn]({link})\n")
    return linhas


def gerar_relatorio_markdown(dados: ProcessedDataOutput, caminho_relatorio: Path) -> None:
    linhas_relatorio = [
        "# 📊 Relatório de Match de Vagas e Posts\n",
        "Este relatório separa oportunidades nacionais e internacionais ordenadas com o maior match primeiro para você focar nas melhores vagas!\n",
        "> **Legenda Motivacional de Match:**\n"
        "> - 🔥 **90% - 100%**: Match Perfeito / Altíssima Aderência (Prioridade Máxima)\n"
        "> - 🚀 **80% - 89%**: Match Excelente (Forte alinhamento técnico)\n"
        "> - ⚡ **70% - 79%**: Match Alto (Boa aderência às tecnologias principais)\n"
        "> - 🎯 **60% - 69%**: Match Qualificado (Atinge requisitos mínimos do perfil)\n"
        "> - 💡 **40% - 59%**: Match Médio\n"
        "> - ⚪ **< 40%**: Match Baixo\n",
        "---\n",
    ]

    secoes = [
        ("nacional", "🇧🇷 Oportunidades Nacionais (Brasil)", dados.nacional),
        ("internacional", "🌐 Oportunidades Internacionais (Gringa)", dados.internacional),
    ]

    for _, nome_escopo, container in secoes:
        linhas_relatorio.append(f"# {nome_escopo}\n")

        # 1. Vagas Formais (Ordenadas pelo maior match primeiro)
        jobs_ordenados = sorted(container.jobs, key=_obter_chave_ordenacao, reverse=True)
        linhas_relatorio.append(
            f"## 📌 Vagas Formais (Jobs) (Total com Match ≥ {dados.filtro_threshold_minimo}%: {len(jobs_ordenados)})\n"
        )
        if not jobs_ordenados:
            linhas_relatorio.append(
                f"_Nenhuma vaga formal encontrada com match mínimo de {dados.filtro_threshold_minimo}%._\n"
            )
        else:
            for indice_vaga, job_item in enumerate(jobs_ordenados, 1):
                linhas_relatorio.extend(
                    _formatar_item_markdown(
                        indice=indice_vaga,
                        item=job_item,
                        titulo=job_item.titulo,
                        empresa=job_item.empresa,
                        localizacao=job_item.localizacao,
                        data_postagem=job_item.data_postagem,
                        link=job_item.link,
                        match_curriculo=job_item.match_curriculo,
                    )
                )

        # 2. Posts (Ordenados pelo maior match primeiro)
        posts_ordenados = sorted(container.post, key=_obter_chave_ordenacao, reverse=True)
        linhas_relatorio.append(
            f"## 💬 Posts do LinkedIn (Total exibido: {len(posts_ordenados)})\n"
        )
        if not posts_ordenados:
            linhas_relatorio.append("_Nenhum post encontrado nesta categoria._\n")
        else:
            for indice_post, post_item in enumerate(posts_ordenados, 1):
                linhas_relatorio.extend(
                    _formatar_item_markdown(
                        indice=indice_post,
                        item=post_item,
                        titulo=post_item.titulo,
                        empresa=post_item.empresa,
                        localizacao=post_item.localizacao,
                        data_postagem=post_item.data_postagem,
                        link=post_item.link,
                        match_curriculo=post_item.match_curriculo,
                    )
                )

        linhas_relatorio.append("---\n")

    caminho_relatorio.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho_relatorio, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(linhas_relatorio))

    logger.info(
        f"📄 Relatório formatado em Markdown gerado com sucesso em '{caminho_relatorio}'."
    )

