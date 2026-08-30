import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

SKILLS_BACKEND = {
    "python": "Python",
    "django": "Django",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mysql": "MySQL",
    "sql": "SQL",
    "redis": "Redis",
    "rabbitmq": "RabbitMQ",
    "celery": "Celery",
    "docker": "Docker",
    "linux": "Linux",
    "aws": "AWS",
    "gcp": "GCP",
    "azure": "Azure",
    "pytest": "Pytest",
    "selenium": "Selenium",
    "jenkins": "Jenkins",
    "gitlab": "GitLab CI",
    "rest": "REST APIs",
    "api": "REST APIs",
    "microservices": "Microservices",
    "microsserviços": "Microservices",
    "git": "Git",
    "vertex ai": "Vertex AI",
    "langchain": "LangChain",
    "pandas": "Pandas"
}

SKILLS_FULLSTACK = {
    "python": "Python",
    "django": "Django",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "vue": "Vue.js",
    "vue.js": "Vue.js",
    "vue 2": "Vue.js",
    "vue 3": "Vue.js",
    "react": "React.js",
    "react.js": "React.js",
    "typescript": "TypeScript",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "html": "HTML/CSS",
    "css": "HTML/CSS",
    "postgresql": "PostgreSQL",
    "mysql": "MySQL",
    "sql": "SQL",
    "redis": "Redis",
    "rabbitmq": "RabbitMQ",
    "celery": "Celery",
    "docker": "Docker",
    "jenkins": "Jenkins",
    "gitlab": "GitLab CI",
    "pytest": "Pytest",
    "jest": "Jest",
    "rest": "REST APIs",
    "api": "REST APIs",
    "aws": "AWS",
    "gcp": "GCP",
    "vertex ai": "Vertex AI",
    "langchain": "LangChain"
}

def calcular_nivel_match(score: int) -> str:
    if score >= 80:
        return "Excelente"
    if score >= 60:
        return "Alto"
    if score >= 40:
        return "Médio"
    return "Baixo"

def calcular_match(vaga: dict, skills_dict: dict, foco: str) -> dict:
    texto = f"{vaga.get('titulo', '')} {vaga.get('descricao_completa', '')}".lower()

    habilidades_encontradas = set()
    for kw, skill_name in skills_dict.items():
        pattern = r'\b' + re.escape(kw) + r'\b'
        if re.search(pattern, texto):
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
        "JavaScript" in habilidades_encontradas)
        ) or (
        foco == "backend" and (
            "Redis" in habilidades_encontradas or
            "RabbitMQ" in habilidades_encontradas or
            "Celery" in habilidades_encontradas or
            "Microservices" in habilidades_encontradas
        )):
        pontos += 15

    score_final = min(100, max(15, pontos)) if "Python" in habilidades_encontradas else min(50, pontos)

    return {
        "score_porcentagem": score_final,
        "nivel": calcular_nivel_match(score_final),
        "habilidades_compativeis": habilidades_lista,
        "total_habilidades_encontradas": len(habilidades_lista)
    }


def normalizar_tipo(item_tipo: str | None) -> str:
    tipo = (item_tipo or "jobs").strip().lower()
    if tipo in {"job", "jobs"}:
        return "jobs"
    if tipo in {"post", "posts"}:
        return "post"
    return "jobs"


def deve_incluir_item(item: dict, match_backend: dict, match_fullstack: dict) -> bool:
    tipo = normalizar_tipo(item.get("tipo"))
    if tipo == "post":
        return True
    return match_backend["score_porcentagem"] >= 60 or match_fullstack["score_porcentagem"] >= 60


def gerar_relatorio_markdown(dados: dict, caminho_relatorio: Path = "relatorio_matches.md"):
    """
    Gera um relatório formatado em Markdown categorizado por Escopo (Nacional/Internacional)
    e Tipo (Jobs/Posts), aplicando o threshold de 60% de match.
    """
    lines = [
        "# 📊 Relatório de Match de Vagas e Posts\n",
        "Este relatório separa vagas normais e posts: as vagas formais usam o threshold de 60%, enquanto os posts são exibidos completos.\n",
        "---\n"
    ]

    for escopo, nome_escopo in [("nacional", "🇧🇷 Oportunidades Nacionais (Brasil)"), ("internacional", "🌐 Oportunidades Internacionais (Gringa)")]:
        lines.append(f"# {nome_escopo}\n")
        escopo_data = dados.get(escopo, {})

        for tipo, nome_tipo in [("jobs", "📌 Vagas Formais (Jobs)"), ("post", "💬 Posts do LinkedIn")]:
            lista = escopo_data.get(tipo, [])
            if tipo == "jobs":
                lines.append(f"## {nome_tipo} (Total com Match ≥ 60%: {len(lista)})\n")
            else:
                lines.append(f"## {nome_tipo} (Total exibido: {len(lista)})\n")

            if not lista:
                if tipo == "jobs":
                    lines.append("_Nenhuma vaga formal encontrada com match mínimo de 60%._\n")
                else:
                    lines.append("_Nenhum post encontrado nesta categoria._\n")
                continue

            for i, v in enumerate(lista, 1):
                m_be = v["match_curriculo"]["backend"]
                m_fs = v["match_curriculo"]["fullstack"]
                best_score = max(m_be["score_porcentagem"], m_fs["score_porcentagem"])

                perfis_comp = []
                if m_be["score_porcentagem"] >= 60:
                    perfis_comp.append(f"Backend: {m_be['score_porcentagem']}% ({m_be['nivel']})")
                if m_fs["score_porcentagem"] >= 60:
                    perfis_comp.append(f"Full-Stack: {m_fs['score_porcentagem']}% ({m_fs['nivel']})")

                comp_str = " | ".join(perfis_comp) if perfis_comp else "Sem match mínimo para este currículo"
                skills_be = ", ".join(m_be["habilidades_compativeis"]) if m_be["habilidades_compativeis"] else "Python"
                skills_fs = ", ".join(m_fs["habilidades_compativeis"]) if m_fs["habilidades_compativeis"] else "Python"

                lines.append(f"### {i}. {v['titulo']} - **Match Máximo: {best_score}%**")
                lines.append(f"- **Compatibilidade**: {comp_str}")
                lines.append(f"- **Empresa/Autor**: {v['empresa']} | **Local**: {v['localizacao']} | **Postagem**: {v['data_postagem']}")
                lines.append(f"- **Skills Backend**: `{skills_be}`")
                lines.append(f"- **Skills Full-Stack**: `{skills_fs}`")
                lines.append(f"- 🔗 [Ver no LinkedIn]({v['link']})\n")

        lines.append("---\n")

    with open(caminho_relatorio, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"📄 Relatório formatado salvo com sucesso em '{caminho_relatorio}'!")

def processar_vagas_com_curriculo(caminho_json: Path = DATA_DIR / "vagas_linkedin.json"):
    """
    Realiza o pós-processamento calculando o match e filtrando por threshold (60%),
    organizando no formato de categorias nacional/internacional e jobs/posts.
    """
    try:
        with open(caminho_json, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Arquivo '{caminho_json}' não encontrado.")
        return

    # Tratar caso o JSON ainda esteja na estrutura antiga (lista simples em "vagas") ou na nova
    vagas_brutas = []
    if "vagas" in data:
        vagas_brutas = data["vagas"]
    else:
        for esc in ["nacional", "internacional"]:
            for tp in ["jobs", "post"]:
                vagas_brutas.extend(data.get(esc, {}).get(tp, []))

    print(f"\nIniciando Pós-Processamento: Calculando Match para {len(vagas_brutas)} itens...")

    resultado_estruturado = {
        "nacional": {"jobs": [], "post": []},
        "internacional": {"jobs": [], "post": []}
    }

    total_aprovados = 0

    for item in vagas_brutas:
        match_be = calcular_match(item, SKILLS_BACKEND, foco="backend")
        match_fs = calcular_match(item, SKILLS_FULLSTACK, foco="fullstack")

        item["match_curriculo"] = {
            "backend": match_be,
            "fullstack": match_fs
        }

        tipo = normalizar_tipo(item.get("tipo"))
        item["tipo"] = tipo

        escopo = item.get("escopo", "nacional")
        if escopo not in resultado_estruturado:
            escopo = "nacional"

        if deve_incluir_item(item, match_be, match_fs):
            resultado_estruturado[escopo][tipo].append(item)
            total_aprovados += 1

    dados_finais = {
        "filtro_threshold_minimo": 60,
        "total_aprovados": total_aprovados,
        "nacional": resultado_estruturado["nacional"],
        "internacional": resultado_estruturado["internacional"]
    }

    # 1. Salva no JSON principal
    with open(DATA_DIR / "vagas_processadas.json", "w", encoding="utf-8") as f:
        json.dump(dados_finais, f, ensure_ascii=False, indent=4)

    print(f"💾 JSON atualizado com {total_aprovados} itens incluídos (jobs com threshold ≥ 60% + todos os posts) em '{DATA_DIR / "vagas_pos_processadas.json"}'.")

    # 2. Salva o Relatório Markdown dedicado
    gerar_relatorio_markdown(dados_finais, DATA_DIR / "relatorio_matches.md")

if __name__ == "__main__":
    processar_vagas_com_curriculo()

