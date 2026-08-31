from pathlib import Path

from app.core.logging import logger
from app.models.match import ResumeMatch
from app.models.report import ProcessedDataOutput


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
    scores = (
        [match.score_porcentagem for match in match_curriculo.perfis.values()]
        if match_curriculo and match_curriculo.perfis
        else []
    )
    melhor_score = max(scores) if scores else 0

    perfis_compativeis: list[str] = []
    skills_linhas: list[str] = []

    if match_curriculo and match_curriculo.perfis:
        for profile_name, profile_match in match_curriculo.perfis.items():
            nome_exibicao = profile_name.capitalize()
            if profile_match.score_porcentagem >= 60:
                perfis_compativeis.append(
                    f"{nome_exibicao}: {profile_match.score_porcentagem}% ({profile_match.nivel.value})"
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
            perfis_compativeis.append(
                f"Backend: {backend_match.score_porcentagem}% ({backend_match.nivel.value})"
            )
        if fullstack_match and fullstack_match.score_porcentagem >= 60:
            perfis_compativeis.append(
                f"Full-Stack: {fullstack_match.score_porcentagem}% ({fullstack_match.nivel.value})"
            )

    compatibilidade_str = (
        " | ".join(perfis_compativeis)
        if perfis_compativeis
        else "Sem match mínimo para este currículo"
    )

    linhas = [
        f"### {indice}. {titulo} - **Match Máximo: {melhor_score}%**",
        f"- **Compatibilidade**: {compatibilidade_str}",
        f"- **Empresa/Autor**: {empresa} | **Local**: {localizacao} | **Postagem**: {data_postagem}",
    ]
    linhas.extend(skills_linhas)
    linhas.append(f"- 🔗 [Ver no LinkedIn]({link})\n")
    return linhas


def gerar_relatorio_markdown(dados: ProcessedDataOutput, caminho_relatorio: Path) -> None:
    linhas_relatorio = [
        "# 📊 Relatório de Match de Vagas e Posts\n",
        "Este relatório separa vagas normais e posts: as vagas formais usam o threshold de 60%, enquanto os posts são exibidos completos.\n",
        "---\n",
    ]

    secoes = [
        ("nacional", "🇧🇷 Oportunidades Nacionais (Brasil)", dados.nacional),
        ("internacional", "🌐 Oportunidades Internacionais (Gringa)", dados.internacional),
    ]

    for _, nome_escopo, container in secoes:
        linhas_relatorio.append(f"# {nome_escopo}\n")

        # 1. Vagas Formais
        linhas_relatorio.append(
            f"## 📌 Vagas Formais (Jobs) (Total com Match ≥ 60%: {len(container.jobs)})\n"
        )
        if not container.jobs:
            linhas_relatorio.append(
                "_Nenhuma vaga formal encontrada com match mínimo de 60%._\n"
            )
        else:
            for indice_vaga, job_item in enumerate(container.jobs, 1):
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

        # 2. Posts
        linhas_relatorio.append(
            f"## 💬 Posts do LinkedIn (Total exibido: {len(container.post)})\n"
        )
        if not container.post:
            linhas_relatorio.append("_Nenhum post encontrado nesta categoria._\n")
        else:
            for indice_post, post_item in enumerate(container.post, 1):
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
