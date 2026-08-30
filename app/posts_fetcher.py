import json
import time
from pathlib import Path
from typing import Literal

import requests

from app.queries import Gringas, Nacionais

SEARXNG_URL = "http://localhost:8080/search"
DATA_DIR = Path(__file__).parent / "data"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}


def buscar_posts_linkedin(
    query: str, escopo: Literal["nacional", "internacional"], max_resultados: int = 15
) -> list[dict]:
    """
    Busca posts do LinkedIn via instância local do SearXNG (formato JSON).
    """
    posts: list[dict] = []
    vistos: set[str] = set()

    params = {
        "q": query,
        "format": "json",
        "time_range": "week",
        "language": "pt-BR" if escopo == "nacional" else "en",
    }

    try:
        # Como o SearXNG é localhost, não enviamos via proxy rotativo externo
        # O próprio SearXNG se encarrega de contornar bloqueios dos motores
        response = requests.get(SEARXNG_URL, params=params, headers=HEADERS, timeout=10)

        if not response or response.status_code != 200:
            print(f"⚠️ SearXNG retornou status inválido ({response.status_code if response else 'Sem Resposta'}).")
            return posts

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
                    "job_id": f"post_{hash(clean_href) & 0xFFFFFFFF}",
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
                    "raw": res,
                })

                if len(posts) >= max_resultados:
                    break

        time.sleep(0.5)

    except Exception as e:
        print(f"⚠️ Exceção ao buscar posts no SearXNG para query ({query[:30]}...): {e}")

    print(f"🔹 Busca concluída para query ({query[:40]}...): {len(posts)} posts encontrados.")
    return posts


if __name__ == "__main__":
    posts_queries = (
        (Gringas.POSTS_FS, "internacional"),
        (Gringas.POSTS_BE, "internacional"),
        (Nacionais.POSTS_FS, "nacional"),
        (Nacionais.POSTS_BE, "nacional"),
    )
    resultados: list[dict] = []

    for query, escopo in posts_queries:
        print(f"🔎 Buscando posts com query ({escopo}): {query[:50]}...")
        resultados.extend(buscar_posts_linkedin(query, escopo=escopo, max_resultados=30))

    print(f"\nTotal de posts encontrados: {len(resultados)}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_DIR / "test_posts.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=4)
