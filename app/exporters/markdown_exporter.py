from pathlib import Path

from app.core.logging import logger
from app.models.report import ProcessedDataOutput


def _formatar_item_markdown(
    indice: int,
    item: object,
    titulo: str,
    empresa: str,
    localizacao: str,
    data_postagem: str,
    link: str,
    match_curriculo: object | None,
) -> list[str]:
    backend_match = match_curriculo.backend if match_curriculo else None
    fullstack_match = match_curriculo.fullstack if match_curriculo else None
    score_backend = backend_match.score_porcentagem if backend_match else 0
    score_fullstack = fullstack_match.score_porcentagem if fullstack_match else 0
    melhor_score = max(score_backend, score_fullstack)

    perfis_compativeis: list[str] = []
    if backend_match and score_backend >= 60:
        perfis_compativeis.append(f"Backend: {score_backend}% ({backend_match.nivel.value})")
    if fullstack_match and score_fullstack >= 60:
        perfis_compativeis.append(f"Full-Stack: {score_fullstack}% ({fullstack_match.nivel.value})")

    compatibilidade_str = " | ".join(perfis_compativeis) if perfis_compativeis else "Sem match mínimo para este currículo"
    skills_backend = ", ".join(backend_match.habilidades_compativeis) if (backend_match and backend_match.habilidades_compativeis) else "Python"
    skills_fullstack = (
        ", ".join(fullstack_match.habilidades_compativeis)
        if (fullstack_match and fullstack_match.habilidades_compativeis)
        else "Python"
    )

    return [
        f"### {indice}. {titulo} - **Match Máximo: {melhor_score}%**",
        f"- **Compatibilidade**: {compatibilidade_str}",
        f"- **Empresa/Autor**: {empresa} | **Local**: {localizacao} | **Postagem**: {data_postagem}",
        f"- **Skills Backend**: `{skills_backend}`",
        f"- **Skills Full-Stack**: `{skills_fullstack}`",
        f"- 🔗 [Ver no LinkedIn]({link})\n",
    ]


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
        linhas_relatorio.append(f"## 📌 Vagas Formais (Jobs) (Total com Match ≥ 60%: {len(container.jobs)})\n")
        if not container.jobs:
            linhas_relatorio.append("_Nenhuma vaga formal encontrada com match mínimo de 60%._\n")
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
        linhas_relatorio.append(f"## 💬 Posts do LinkedIn (Total exibido: {len(container.post)})\n")
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

    logger.info(f"📄 Relatório formatado em Markdown gerado com sucesso em '{caminho_relatorio}'.")

