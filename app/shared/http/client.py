import urllib.parse

import requests

from app.core.logging import logger
from app.shared.http.proxy_rotator import DEFAULT_HEADERS, rotator


def _is_local_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    hostname = (parsed.hostname or "").lower()
    return hostname in {"localhost", "127.0.0.1", "0.0.0.0", "::1"}  # noqa: S104


def requisicao_com_rotacao(
    url: str,
    usar_proxy: bool,
    timeout: int,
    max_retries: int,
    headers: dict[str, str] | None = None,
    params: dict[str, str] | None = None,
) -> requests.Response | None:
    cabecalhos = headers or DEFAULT_HEADERS
    ultimo_erro: str | None = None
    eh_local = _is_local_url(url)

    # Modo direto (sem proxy): requisição direta simples sem loop excessivo de retries
    if not usar_proxy or eh_local:
        try:
            logger.debug(f"[HTTP] Direto (Sem Proxy) -> {url}")
            response = requests.get(
                url,
                headers=cabecalhos,
                params=params,
                timeout=timeout,
            )
        except requests.RequestException as excecao:
            logger.debug(f"[HTTP] Erro em requisição direta para {url}: {excecao}")
            return None
        else:
            if response.status_code == 200:
                return response
            logger.debug(f"[HTTP] Resposta direta com status {response.status_code} para {url}")
            return None

    # Modo com Proxy: Rotaciona IP a cada tentativa (zero retry com o mesmo IP)
    limite_rotacoes = max_retries
    rotacao_atual = 0

    while rotacao_atual < limite_rotacoes:
        rotacao_atual += 1
        proxy_dict = rotator.obter_proximo_proxy()
        if not proxy_dict:
            logger.warning("[HTTP] Nenhum proxy disponível no pool para realizar a requisição.")
            break

        proxy_url = proxy_dict.get("http", "")
        logger.debug(f"[HTTP] Tentativa {rotacao_atual}/{limite_rotacoes} via {proxy_url} -> {url}")

        try:
            response = requests.get(
                url,
                headers=cabecalhos,
                params=params,
                proxies=proxy_dict,
                timeout=timeout,
            )

            if response.status_code == 200:
                return response

            ultimo_erro = f"Status {response.status_code}"
            logger.debug(f"[HTTP] Status {response.status_code} via {proxy_url} para {url}")

            # Se o proxy tomou 429, 401, 403 ou 5xx, descarta ele imediatamente
            if response.status_code in {401, 403, 429, 500, 502, 503, 504}:
                rotator.remover_proxy_invalido(proxy_url, motivo=f"Status {response.status_code}")

        except requests.RequestException as excecao:
            ultimo_erro = str(excecao)
            logger.debug(f"[HTTP] Erro de rede ({excecao.__class__.__name__}) via {proxy_url} para {url}")
            # Descarta proxy com erro de timeout ou conexão
            rotator.remover_proxy_invalido(proxy_url, motivo=excecao.__class__.__name__)

    logger.warning(f"[HTTP] Falha após {rotacao_atual} rotações de IP para {url}. Último erro: {ultimo_erro}")
    return None
