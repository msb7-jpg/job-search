import json
import re

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
    elif score >= 60:
        return "Alto"
    elif score >= 40:
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

def gerar_relatorio_markdown(vagas: list, caminho_relatorio: str = "relatorio_matches.md"):
    """
    Gera um relatório formatado em Markdown com as vagas ordenadas por compatibilidade.
    """
    vagas_be = sorted(vagas, key=lambda x: x["match_curriculo"]["backend"]["score_porcentagem"], reverse=True)
    vagas_fs = sorted(vagas, key=lambda x: x["match_curriculo"]["fullstack"]["score_porcentagem"], reverse=True)

    lines = [
        "# 📊 Relatório de Match de Vagas com Currículos\n",
        f"**Total de vagas analisadas**: {len(vagas)}\n",
        "---\n",
        "## 🐍 Top Vagas - Perfil Backend Python (`Miguel's Resume - Backend.md`)\n"
    ]

    for i, v in enumerate(vagas_be[:15], 1):
        m = v["match_curriculo"]["backend"]
        skills = ", ".join(m["habilidades_compativeis"]) if m["habilidades_compativeis"] else "Conhecimentos gerais em Python"
        lines.append(f"### {i}. {v['titulo']} - **{m['score_porcentagem']}% ({m['nivel']})**")
        lines.append(f"- **Empresa**: {v['empresa']} | **Local**: {v['localizacao']} | **Postagem**: {v['data_postagem']}")
        lines.append(f"- **Tecnologias Compatíveis**: `{skills}`")
        lines.append(f"- 🔗 [Ver Vaga no LinkedIn]({v['link']})\n")

    lines.append("---\n")
    lines.append("## ⚡ Top Vagas - Perfil Full-Stack (`Miguel's Resume - Full-stack.md`)\n")

    for i, v in enumerate(vagas_fs[:15], 1):
        m = v["match_curriculo"]["fullstack"]
        skills = ", ".join(m["habilidades_compativeis"]) if m["habilidades_compativeis"] else "Conhecimentos gerais em Python"
        lines.append(f"### {i}. {v['titulo']} - **{m['score_porcentagem']}% ({m['nivel']})**")
        lines.append(f"- **Empresa**: {v['empresa']} | **Local**: {v['localizacao']} | **Postagem**: {v['data_postagem']}")
        lines.append(f"- **Tecnologias Compatíveis**: `{skills}`")
        lines.append(f"- 🔗 [Ver Vaga no LinkedIn]({v['link']})\n")

    with open(caminho_relatorio, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"📄 Relatório formatado salvo com sucesso em '{caminho_relatorio}'!")

def processar_vagas_com_curriculo(caminho_json: str = "vagas_linkedin.json"):
    """
    Realiza o pós-processamento das vagas calculando o match e salvando tanto o JSON quanto o relatório Markdown.
    """
    try:
        with open(caminho_json, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Arquivo '{caminho_json}' não encontrado.")
        return

    vagas = data.get("vagas", [])
    print(f"\nIniciando Pós-Processamento: Calculando Match para {len(vagas)} vagas com os Currículos Backend & Full-stack...")

    vagas_processadas = []
    for vaga in vagas:
        match_be = calcular_match(vaga, SKILLS_BACKEND, foco="backend")
        match_fs = calcular_match(vaga, SKILLS_FULLSTACK, foco="fullstack")
        
        vaga["match_curriculo"] = {
            "backend": match_be,
            "fullstack": match_fs
        }
        vagas_processadas.append(vaga)

    data["vagas"] = vagas_processadas
    
    # 1. Salva no JSON principal
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"💾 JSON atualizado com 'match_curriculo' em '{caminho_json}'.")

    # 2. Salva o Relatório Markdown dedicado
    gerar_relatorio_markdown(vagas_processadas, "relatorio_matches.md")

if __name__ == "__main__":
    processar_vagas_com_curriculo()
