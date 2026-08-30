import requests

from app.core.config import Settings, settings as default_settings
from app.core.logging import logger
from app.models.enums import ItemTypeEnum, ScopeEnum, SeniorityEnum, WorkModelEnum
from app.models.post import PostItem
from app.shared.http.proxy_rotator import DEFAULT_HEADERS


def gerar_variantes_query_posts(query: str, max_variantes: int = 4) -> list[str]:
    base = (query or "").strip()
    if not base:
        return []

    variantes: list[str] = []
    primeira = base if base.startswith("site:") else f"site:linkedin.com/posts/ {base}".strip()
    variantes.append(primeira)

    lowered = base.lower()
    if "hiring" in lowered:
        variantes.append(f"{base} AND \"hiring\"")
    if "python" in lowered:
        variantes.append(f"{base} AND \"Python\"")
    if "remote" not in lowered:
        variantes.append(f"{base} AND \"remote\"")

    variantes_unicas: list[str] = []
    visto: set[str] = set()
    for variante in variantes:
        chave = variante.strip()
        if not chave or chave in visto:
            continue
        visto.add(chave)
        variantes_unicas.append(chave)
        if len(variantes_unicas) >= max_variantes:
            break

    return variantes_unicas


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
        post_item = PostItem(
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
            descricao_completa=snippet
        )
        posts.append(post_item)
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

    try:
        response = requests.get(
            cfg.searxng_url,
            params={**params_base, "q": query},
            headers=DEFAULT_HEADERS,
            timeout=cfg.searxng_timeout,
        )
        if response.status_code != 200:
            return []

        posts = _converter_resultados_em_posts(response.json().get("results", []), scope, max_resultados)
        if posts:
            logger.info(f"[POSTS-FETCHER] Encontrados {len(posts)} posts para variante: '{query[:35]}...'")
            return posts
    except (requests.RequestException, ValueError) as exc:
        logger.warning(f"[POSTS-FETCHER] Exceção ao consultar SearXNG: {exc}")

    logger.info(f"[POSTS-FETCHER] Nenhum post retornado para: '{query[:40]}...'")
    return []
