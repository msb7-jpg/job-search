import time
from typing import Literal

import requests

SEARXNG_URL = "http://localhost:8080/search"

def buscar_posts_linkedin(query: str, escopo: Literal["nacional", "internacional"], max_resultados: int = 15) -> list[dict]:
    """
    Busca posts do LinkedIn via instância local do SearXNG (formato JSON).
    """
    posts = []
    vistos = set()

    params = {
        "q": query,
        "format": "json",
        "time_range": "week",  # Equivalente ao timelimit="w"
        "language": "pt-BR"
    }

    try:
        response = requests.get(SEARXNG_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        resultados = data.get("results", [])

        for res in resultados:
            href = res.get("url", "")
            clean_href = href.split("?")[0]

            # Filtra apenas URLs válidas de posts ou updates
            if "linkedin.com/posts" in clean_href or "linkedin.com/feed/update" in clean_href:
                if clean_href in vistos:
                    continue
                vistos.add(clean_href)

                titulo = res.get("title", "Post no LinkedIn")
                snippet = res.get("content", "")

                posts.append({
                    "job_id": f"post_{hash(clean_href) & 0xffffffff}",
                    "tipo": "post",
                    "escopo": escopo,
                    "titulo": titulo,
                    "empresa": "LinkedIn Post",
                    "localizacao": "Brasil" if escopo == "nacional" else "Remoto / LATAM / Global",
                    "data_postagem": res.get("publishedDate", "Recente"),
                    "senioridade": "Júnior",
                    "modelo_trabalho": "Remoto",
                    "link": clean_href,
                    "descricao_resumida": snippet,
                    "descricao_completa": snippet,
                    "raw": res
                })

                if len(posts) >= max_resultados:
                    break

        time.sleep(0.5)

    except Exception as e:
        print(f"⚠️ Exceção ao buscar posts no SearXNG para query ({query[:30]}...): {e}")

    print(f"🔹 Busca concluída para query ({query}...): {len(posts)} posts encontrados.")
    return posts


if __name__ == "__main__":
    # Teste rápido da função
    POSTS_QUERY = (
    'site:linkedin.com/posts/ "hiring" and ("vue" or "react") and "python" and "remote" '
    '-pleno -pl -senior -sr -ssr -staff -lead -principal -architect -staff '
    '-lead -c2c -"us based" -hybrid -site -"us only" -"no visa" '
    '-"citizens only" -"security clearance" -"on-site" -"local only" '
    '-"must be located"'
)

    resultados = buscar_posts_linkedin(POSTS_QUERY, "internacional", max_resultados=5)
    for post in resultados:
        print(post)

    with open("test_posts.json", "w", encoding="utf-8") as f:
        import json
        json.dump(resultados, f, ensure_ascii=False, indent=4)
