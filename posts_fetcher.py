import time

from ddgs import DDGS


def buscar_posts_linkedin(query: str, escopo: str, max_resultados: int = 15) -> list[dict]:
    """
    Busca posts do LinkedIn via DuckDuckGo Search (sem necessidade de API Key).
    """
    posts = []
    vistos = set()

    # Sanitização leve da query para o DuckDuckGo
    query_ddg = query.replace("site:linkedin.com/posts", "site:linkedin.com/posts/")

    try:
        with DDGS() as ddgs:
            resultados = ddgs.text(query_ddg, max_results=max_resultados * 2)

            if not resultados:
                return posts

            for res in resultados:
                href = res.get("href", "")
                clean_href = href.split("?")[0]

                # Filtra apenas URLs válidas de posts ou updates
                if "linkedin.com/posts" in clean_href or "linkedin.com/feed/update" in clean_href:
                    if clean_href in vistos:
                        continue
                    vistos.add(clean_href)

                    titulo = res.get("title", "Post no LinkedIn")
                    snippet = res.get("body", "")

                    posts.append({
                        "job_id": f"post_{hash(clean_href) & 0xffffffff}",
                        "tipo": "post",
                        "escopo": escopo,
                        "titulo": titulo,
                        "empresa": "LinkedIn Post",
                        "localizacao": "Brasil" if escopo == "nacional" else "Remoto / LATAM / Global",
                        "data_postagem": "Recente",
                        "senioridade": "Júnior",
                        "modelo_trabalho": "Remoto",
                        "link": clean_href,
                        "descricao_resumida": snippet,
                        "descricao_completa": snippet
                    })

                    if len(posts) >= max_resultados:
                        break

        # Pequena pausa defensiva para evitar bloqueio por taxa de requisições
        time.sleep(1)

    except Exception as e:
        print(f"⚠️ Exceção ao buscar posts no DuckDuckGo para query ({query[:30]}...): {e}")

    return posts
