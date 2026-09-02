import urllib.parse

import requests
from bs4 import BeautifulSoup
from googlesearch import SearchResult, search

from app.core.config import Settings
from app.core.logging import logger
from app.jobs.classifiers import classificar_modelo_trabalho, classificar_senioridade, pre_filtrar_post_bruto
from app.models.enums import ItemTypeEnum, ScopeEnum
from app.models.post import PostItem
from app.shared.http.proxy_rotator import rotator

GOOGLE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
    "Sec-Ch-Ua": '"Not-A.Brand";v="99", "Chromium";v="124", "Google Chrome";v="124"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
}

GOOGLE_COOKIES = {
    "CONSENT": "PENDING+987",
    "SOCS": "CAESHAgBEhIaAB",
}


def formatar_query(query: str) -> str | None:
    if not (base := query or "").strip():
        return None

    if "site:linkedin.com/posts" in base or "site:linkedin.com/feed" in base or "site:linkedin.com" in base:
        return base.strip()

    return f"site:linkedin.com/posts/ {base}".strip()


def _extrair_posts_de_html(html: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    resultados: list[dict[str, str]] = []
    vistos: set[str] = set()

    for a_tag in soup.find_all("a", href=True):
        raw_href = a_tag["href"]
        if "/url?q=" in raw_href:
            raw_href = urllib.parse.unquote(raw_href.split("/url?q=")[1].split("&")[0])
        clean_href = raw_href.split("?")[0].rstrip("/")

        if not ("linkedin.com/posts" in clean_href or "linkedin.com/feed/update" in clean_href):
            continue
        if clean_href in vistos:
            continue
        vistos.add(clean_href)

        h3_tag = a_tag.find("h3")
        titulo = h3_tag.get_text(strip=True) if h3_tag else a_tag.get_text(strip=True)
        if not titulo or len(titulo) < 3:
            titulo = "Post no LinkedIn"

        container = a_tag
        for _ in range(4):
            if container.parent:
                container = container.parent
                classes = container.get("class", [])
                if any(c in classes for c in ["g", "tF2Cxc", "MjjYud"]):
                    break

        descricao = ""
        for element in container.find_all(["div", "span"]):
            text = element.get_text(strip=True)
            if len(text) > 25 and text != titulo and not text.startswith("http"):
                descricao = text
                break

        resultados.append({"href": clean_href, "title": titulo, "body": descricao})

    return resultados


def _converter_resultados_em_posts(
    resultados: list[dict[str, str]],
    scope: ScopeEnum,
    max_resultados: int,
    settings: Settings,
) -> list[PostItem]:
    posts: list[PostItem] = []
    vistos: set[str] = set()

    for item in resultados:
        href = item.get("href") or item.get("url") or ""
        clean_href = href.split("?", 1)[0].rstrip("/")
        if not ("linkedin.com/posts" in clean_href or "linkedin.com/feed/update" in clean_href):
            continue
        if clean_href in vistos:
            continue
        vistos.add(clean_href)

        snippet = item.get("body") or item.get("description") or item.get("content") or ""
        titulo = item.get("title") or "Post no LinkedIn"
        localizacao = "Brasil" if scope == ScopeEnum.NACIONAL else "Remoto / LATAM / Global"

        if not pre_filtrar_post_bruto(
            titulo=titulo,
            descricao=snippet,
            localizacao=localizacao,
            apenas_remoto=settings.apenas_remoto,
            senioridade_filtro=settings.senioridade_filtro,
        ):
            continue

        senioridade = classificar_senioridade(
            titulo=titulo,
            descricao=snippet,
            padrao_junior=(settings.senioridade_filtro == "JUNIOR"),
        )
        modelo_trabalho = classificar_modelo_trabalho(
            titulo=titulo,
            localizacao=localizacao,
            descricao=snippet,
            padrao_remoto=settings.apenas_remoto,
        )

        post_item = PostItem(
            job_id=f"post_{hash(clean_href) & 0xFFFFFFFF}",
            tipo=ItemTypeEnum.POST,
            escopo=scope,
            titulo=titulo,
            empresa="LinkedIn Post",
            localizacao=localizacao,
            data_postagem="Recente",
            senioridade=senioridade,
            modelo_trabalho=modelo_trabalho,
            link=clean_href,
            descricao_resumida=snippet,
            descricao_completa=snippet,
        )
        posts.append(post_item)
        if len(posts) >= max_resultados:
            break

    return posts


def _normalizar_item_resultado(item: SearchResult | dict | str) -> dict[str, str]:
    if isinstance(item, SearchResult):
        return {
            "href": item.url,
            "title": item.title,
            "body": item.description,
        }
    if isinstance(item, dict):
        return {
            "href": item.get("href") or item.get("url") or "",
            "title": item.get("title") or "",
            "body": item.get("body") or item.get("description") or "",
        }
    if isinstance(item, str):
        return {"href": item, "title": "", "body": ""}
    return {"href": "", "title": "", "body": ""}


def _tratar_erro_google_search(erro: Exception, proxy_str: str | None, status_code: int | None = None) -> bool:
    if proxy_str:
        motivo = f"Google HTTP {status_code}" if status_code else erro.__class__.__name__
        rotator.remover_proxy_invalido(proxy_str, motivo=motivo)
        return False
    return status_code in {401, 403, 429}


def _executar_busca_direta_google(
    clean_query: str,
    lang: str,
    region: str,
    tbs: str | None,
    proxy_str: str | None,
    timeout: float,
) -> list[dict[str, str]]:
    params: dict[str, str | int] = {
        "q": clean_query,
        "hl": lang,
        "gl": region,
        "num": 25,
    }
    if tbs:
        params["tbs"] = tbs

    proxies = {"http": proxy_str, "https": proxy_str} if proxy_str else None
    response = requests.get(
        "https://www.google.com/search",
        params=params,
        headers=GOOGLE_HEADERS,
        cookies=GOOGLE_COOKIES,
        proxies=proxies,
        timeout=timeout,
    )
    if response.status_code == 200:
        return _extrair_posts_de_html(response.text)

    response.raise_for_status()
    return []


def _executar_busca_fallback_lib(
    clean_query: str,
    lang: str,
    region: str,
    proxy_str: str | None,
    max_resultados: int,
    timeout: float,
) -> list[dict[str, str]]:
    itens = list(
        search(
            term=clean_query,
            num_results=max_resultados,
            lang=lang,
            region=region,
            proxy=proxy_str,
            advanced=True,
            timeout=timeout,
            sleep_interval=0,
            unique=True,
        )
    )
    resultados: list[dict[str, str]] = []
    for item in itens:
        normalizado = _normalizar_item_resultado(item)
        if normalizado["href"]:
            resultados.append(normalizado)
    return resultados


def buscar_posts_linkedin(
    query: str,
    scope: ScopeEnum,
    settings: Settings,
    max_resultados: int = 15,
) -> list[PostItem]:
    """Busca publicações do LinkedIn via Google Search com suporte a rotação dinâmica de proxies e filtro de data."""
    cfg = settings
    region = "br" if scope == ScopeEnum.NACIONAL else "us"
    lang = "pt" if scope == ScopeEnum.NACIONAL else "en"
    tbs = cfg.filtro_tempo.google_tbs

    logger.debug(f"[POSTS-FETCHER] Executando busca de posts ({scope}) via Google Search para: {query[:45]}...")

    if not (clean_query := formatar_query(query)):
        logger.warning(f"[POSTS-FETCHER] Query inválida ou vazia para buscar posts: '{query[:40]}...'")
        return []

    max_tentativas = 5 if cfg.usar_proxy else 2
    tentativa = 0
    resultados_brutos: list[dict[str, str]] = []

    while tentativa < max_tentativas:
        tentativa += 1
        proxy_str = rotator.obter_proxima_string_proxy() if (cfg.usar_proxy and rotator.total_valid > 0) else None
        proxy_desc = proxy_str or "Direto (Sem Proxy)"

        logger.debug(f"[POSTS-FETCHER] Tentativa {tentativa}/{max_tentativas} via {proxy_desc} para: '{clean_query[:40]}...'")

        try:
            # 1. Tentativa via motor direto de extração DOM com headers de navegador e tbs
            resultados_brutos = _executar_busca_direta_google(
                clean_query=clean_query,
                lang=lang,
                region=region,
                tbs=tbs,
                proxy_str=proxy_str,
                timeout=cfg.http_timeout,
            )
            if not resultados_brutos:
                # 2. Fallback via googlesearch lib
                resultados_brutos = _executar_busca_fallback_lib(
                    clean_query=clean_query,
                    lang=lang,
                    region=region,
                    proxy_str=proxy_str,
                    max_resultados=max_resultados,
                    timeout=cfg.http_timeout,
                )
            break

        except requests.exceptions.HTTPError as erro:
            status_code = getattr(erro.response, "status_code", None)
            logger.warning(f"[POSTS-FETCHER] HTTP {status_code} no Google Search via {proxy_desc}: {erro}")
            if _tratar_erro_google_search(erro, proxy_str, status_code):
                break

        except (requests.exceptions.RequestException, TimeoutError) as erro:
            logger.warning(f"[POSTS-FETCHER] Falha de conexão no Google Search via {proxy_desc}: {erro}")
            if _tratar_erro_google_search(erro, proxy_str):
                break

        except Exception as erro:
            logger.warning(f"[POSTS-FETCHER] Erro inesperado no Google Search via {proxy_desc}: {erro}")
            if proxy_str:
                rotator.remover_proxy_invalido(proxy_str)
            break

    if posts := _converter_resultados_em_posts(resultados_brutos, scope, max_resultados, cfg):
        logger.info(f"[POSTS-FETCHER] Encontrados {len(posts)} posts para query: '{query[:35]}...'")
        return posts

    logger.info(f"[POSTS-FETCHER] Nenhum post retornado para: '{query[:40]}...'")
    return []
