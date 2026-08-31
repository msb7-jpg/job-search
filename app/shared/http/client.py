import time
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
    headers: dict[str, str] | None = None,
    params: dict[str, str] | None = None,
    max_retries: int = 5,
    timeout: int = 8,
    usar_proxy: bool = False,
) -> requests.Response | None:
    headers = headers or DEFAULT_HEADERS
    ultimo_erro: str | None = None
    eh_local = _is_local_url(url)

    for tentativa in range(1, max_retries + 1):
        proxy = (
            rotator.obter_proximo_proxy()
            if (usar_proxy and not eh_local and bool(rotator.valid_proxies))
            else None
        )
        proxy_descricao = proxy.get("http") if proxy else "Direto (Sem Proxy)"

        logger.debug(f"[HTTP] Tentativa {tentativa}/{max_retries} via {proxy_descricao} -> {url}")
        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                proxies=proxy,
                timeout=timeout,
            )

            if response.status_code == 200:
                return response

            ultimo_erro = f"Status {response.status_code}"
            logger.debug(f"[HTTP] Resposta com status {response.status_code} para {url}")

            if response.status_code in {401, 403, 429}:
                break

        except requests.RequestException as excecao:
            ultimo_erro = str(excecao)
            logger.debug(f"[HTTP] Erro de rede ({excecao.__class__.__name__}) para {url}")

        if tentativa < max_retries:
            time.sleep(min(0.25 * tentativa, 1.0))

    logger.warning(f"[HTTP] Falha após {max_retries} tentativas para {url}. Último erro: {ultimo_erro}")
    return None
