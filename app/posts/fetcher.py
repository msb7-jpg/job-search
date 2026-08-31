import ddgs
import ddgs.exceptions

from app.core.config import Settings, settings as default_settings
from app.core.logging import logger
from app.models.enums import ItemTypeEnum, ScopeEnum, SeniorityEnum, WorkModelEnum
from app.models.post import PostItem


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

    for item in resultados:
        href = item.get("href") or item.get("url") or ""
        clean_href = href.split("?", 1)[0]
        if not ("linkedin.com/posts" in clean_href or "linkedin.com/feed/update" in clean_href):
            continue
        if clean_href in vistos:
            continue
        vistos.add(clean_href)

        snippet = item.get("body") or item.get("content") or ""
        post_item = PostItem(
            job_id=f"post_{hash(clean_href) & 0xFFFFFFFF}",
            tipo=ItemTypeEnum.POST,
            escopo=scope,
            titulo=item.get("title", "Post no LinkedIn"),
            empresa="LinkedIn Post",
            localizacao="Brasil" if scope == ScopeEnum.NACIONAL else "Remoto / LATAM / Global",
            data_postagem="Recente",
            senioridade=SeniorityEnum.JUNIOR,
            modelo_trabalho=WorkModelEnum.REMOTO,
            link=clean_href,
            descricao_resumida=snippet,
            descricao_completa=snippet,
        )
        posts.append(post_item)
        if len(posts) >= max_resultados:
            break

    return posts


def buscar_posts_linkedin(
    query: str,
    scope: ScopeEnum,
    max_resultados: int = 15,
    settings: Settings | None = None,
) -> list[PostItem]:
    cfg = settings or default_settings
    region = "br-pt" if scope == ScopeEnum.NACIONAL else "wt-wt"
    timelimit = cfg.filtro_tempo.ddgs_timelimit

    logger.debug(f"[POSTS-FETCHER] Executando busca de posts ({scope}) via DDGS para: {query[:45]}...")

    try:
        ddgs_client = ddgs.DDGS(timeout=cfg.http_timeout)
        resultados_brutos = ddgs_client.text(
            query=query,
            region=region,
            timelimit=timelimit,
            max_results=max_resultados,
        )
    except ddgs.exceptions.TimeoutException as e:
        logger.warning(f"[POSTS-FETCHER] Timeout ao buscar posts para: '{query[:40]}...'. Erro: {e}")
        return []

    if posts := _converter_resultados_em_posts(resultados_brutos, scope, max_resultados):
        logger.info(f"[POSTS-FETCHER] Encontrados {len(posts)} posts para query: '{query[:35]}...'")
        return posts


    logger.info(f"[POSTS-FETCHER] Nenhum post retornado para: '{query[:40]}...'")
    return []
