import time

import requests

from app.core.logging import logger
from app.shared.http.proxy_rotator import DEFAULT_HEADERS, rotator


def requisicao_com_rotacao(
    url: str,
    headers: dict[str, str] | None = None,
    params: dict[str, str] | None = None,
    max_retries: int = 8,
    timeout: int = 8
) -> requests.Response | None:
    headers = headers or DEFAULT_HEADERS
    last_error: str | None = None

    for tentativa in range(1, max_retries + 1):
        proxy = None if (tentativa == max_retries and rotator.valid_proxies) else rotator.obter_proximo_proxy()
        proxy_str = proxy.get("http") if proxy else "Direto (Sem Proxy)"

        logger.debug(f"[HTTP] Tentativa {tentativa}/{max_retries} via {proxy_str} -> {url}")
        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                proxies=proxy,
                timeout=timeout,
            )

            if response.status_code == 200 and (proxy is None or rotator._proxy_response_looks_valid(response)):
                return response

            last_error = f"Status {response.status_code}"
            logger.debug(f"[HTTP] Resposta inválida/bloqueio ({last_error}). Alternando rota...")

        except requests.RequestException as exc:
            last_error = str(exc)
            logger.debug(f"[HTTP] Erro de rede ({exc.__class__.__name__}). Alternando rota...")

        if tentativa < max_retries:
            time.sleep(0.4 * tentativa)

    logger.warning(f"[HTTP] Falha após {max_retries} tentativas para {url}. Último erro: {last_error}")
    return None
