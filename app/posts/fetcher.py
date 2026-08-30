import requests

from app.core.config import Settings, settings as default_settings
from app.core.logging import logger
from app.models.enums import ItemTypeEnum, ScopeEnum, SeniorityEnum, WorkModelEnum
from app.models.post import PostItem
from app.shared.http.proxy_rotator import DEFAULT_HEADERS


def gerar_variantes_query_posts(query: str) -> list[str]:
    variantes = [query]
    sem_filtro_site = query.replace("site:linkedin.com/posts/", "")
    if sem_filtro_site != query:
        variantes.append(sem_filtro_site)

    sem_termos_exclusao = sem_filtro_site.split(" -", 1)[0]
    if sem_termos_exclusao not in variantes:
        variantes.append(sem_termos_exclusao)

    return list(dict.fromkeys(variantes))

def _converter_resultados_em_posts(
    resultados: list[dict], scope: ScopeEnum, max_resultados: int
) -> list[PostItem]:
    posts: list[PostItem] = []
    vistos: set[str] = set()

    for res in resultados:
        href = res.get("url", "")
        clean_href = href.split("?", 1)[0]
        if not ("linkedin.com/posts" in clean_href or "linkedin.com/feed/update" in clean_href):
            continue
        if clean_href in vistos:
            continue
        vistos.add(clean_href)

        snippet = res.get("content", "")
        posts.append(PostItem(
            job_id=f"post_{hash(clean_href) & 0xFFFFFFFF}",
            tipo=ItemTypeEnum.POST,
            escopo=scope,
            titulo=res.get("title", "Post no LinkedIn"),
            empresa="LinkedIn Post",
            localizacao="Brasil" if scope == ScopeEnum.NACIONAL else "Remoto / LATAM / Global",
            data_postagem=res.get("publishedDate", "Recente"),
            senioridade=SeniorityEnum.JUNIOR,
            modelo_trabalho=WorkModelEnum.REMOTO,
            link=clean_href,
            descricao_resumida=snippet,
            descricao_completa=snippet,
            raw=res,
        ))
        if len(posts) >= max_resultados:
            break

    return posts

def buscar_posts_linkedin(
    query: str,
    scope: ScopeEnum,
    max_resultados: int = 15,
    settings: Settings | None = None
) -> list[PostItem]:
    cfg = settings or default_settings
    params_base = {
        "format": "json",
        "time_range": "week",
        "language": "pt-BR" if scope == ScopeEnum.NACIONAL else "en",
    }

    logger.debug(f"[POSTS-FETCHER] Executando busca de posts ({scope}) para: {query[:45]}...")

    for variante in gerar_variantes_query_posts(query):
        try:
            response = requests.get(
                cfg.searxng_url,
                params={**params_base, "q": variante},
                headers=DEFAULT_HEADERS,
                timeout=cfg.searxng_timeout,
            )
            if response.status_code != 200:
                continue

            posts = _converter_resultados_em_posts(response.json().get("results", []), scope, max_resultados)
            if posts:
                logger.info(f"[POSTS-FETCHER] Encontrados {len(posts)} posts para variante: '{variante[:35]}...'")
                return posts
        except (requests.RequestException, ValueError) as exc:
            logger.warning(f"[POSTS-FETCHER] Exceção ao consultar SearXNG: {exc}")

    logger.info(f"[POSTS-FETCHER] Nenhum post retornado para: '{query[:40]}...'")
    return []
