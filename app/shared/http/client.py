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
    cabecalhos = headers or DEFAULT_HEADERS
    ultimo_erro: str | None = None
    eh_local = _is_local_url(url)

    tentativas_limite = max_retries
    tentativa = 0

    while tentativa < tentativas_limite:
        tentativa += 1
        proxy_dict = (
            rotator.obter_proximo_proxy()
            if (usar_proxy and not eh_local and rotator.total_valid > 0)
            else None
        )
        proxy_url = proxy_dict.get("http") if proxy_dict else None
        proxy_descricao = proxy_url or "Direto (Sem Proxy)"

        logger.debug(f"[HTTP] Tentativa {tentativa}/{tentativas_limite} via {proxy_descricao} -> {url}")
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
            logger.debug(f"[HTTP] Resposta com status {response.status_code} para {url}")

            # Se o proxy tomou 401/403/429, descarta esse proxy e roda o próximo se houver
            if proxy_url and response.status_code in {401, 403, 429}:
                rotator.remover_proxy_invalido(proxy_url)
                if rotator.total_valid > 0 and tentativa >= tentativas_limite:
                    tentativas_limite += 1  # Permite continuar enquanto houver proxies saudáveis
            elif not proxy_url and response.status_code in {401, 403, 429}:
                break

        except requests.RequestException as excecao:
            ultimo_erro = str(excecao)
            logger.debug(f"[HTTP] Erro de rede ({excecao.__class__.__name__}) para {url} via {proxy_descricao}")
            # Descarta proxy quebrado imediatamente
            if proxy_url:
                rotator.remover_proxy_invalido(proxy_url)
                if rotator.total_valid > 0 and tentativa >= tentativas_limite:
                    tentativas_limite += 1

        if tentativa < tentativas_limite:
            time.sleep(min(0.2 * tentativa, 0.6))

    logger.warning(f"[HTTP] Falha após {tentativa} tentativas para {url}. Último erro: {ultimo_erro}")
    return None
