import time
import urllib.parse

import requests

from app.core.logging import logger
from app.shared.http.proxy_rotator import DEFAULT_HEADERS, rotator
from app.shared.http.proxy_sources import INVALID_PROXY_BODY_MARKERS


def _is_local_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    hostname = (parsed.hostname or "").lower()
    return hostname in {"localhost", "127.0.0.1", "0.0.0.0", "::1"}  # noqa: S104


def _is_valid_target_payload(response_text: str) -> bool:
    """Verifica se um HTTP 200 retornado via proxy não é uma página de interceptação/bloqueio de proxy."""
    sample = (response_text or "")[:1500].lower()
    if not sample.strip():
        return True
    return all(marker not in sample for marker in INVALID_PROXY_BODY_MARKERS)


def _executar_requisicao_direta(
    url: str,
    cabecalhos: dict[str, str],
    params: dict[str, str] | None,
    timeout: int | tuple[float, float],
) -> requests.Response | None:
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
    if response.status_code == 200:
        return response
    logger.debug(f"[HTTP] Resposta direta com status {response.status_code} para {url}")
    return None


def requisicao_com_rotacao(
    url: str,
    usar_proxy: bool,
    timeout: int,
    max_retries: int,
    headers: dict[str, str] | None = None,
    params: dict[str, str] | None = None,
    fallback_direto: bool = True,
) -> requests.Response | None:
    cabecalhos = headers or DEFAULT_HEADERS
    ultimo_erro: str | None = None
    eh_local = _is_local_url(url)

    # Modo direto (sem proxy): requisição direta simples sem loop excessivo de retries
    if not usar_proxy or eh_local:
        return _executar_requisicao_direta(url, cabecalhos, params, timeout)

    # Modo Reativo com Proxy + Inline Circuit Breaker
    limite_rotacoes = max(1, max_retries)
    rotacao_atual = 0
    connect_timeout = min(2.2, float(timeout))
    read_timeout = max(2.5, float(timeout))
    timeout_tupla = (connect_timeout, read_timeout)

    while rotacao_atual < limite_rotacoes:
        rotacao_atual += 1
        proxy_dict = rotator.obter_proximo_proxy()
        if not proxy_dict:
            logger.debug("[HTTP] Nenhum proxy disponível no pool no momento.")
            break

        proxy_url = proxy_dict.get("http", "")
        logger.debug(f"[HTTP] Tentativa {rotacao_atual}/{limite_rotacoes} via {proxy_url} -> {url}")
        inicio_req = time.perf_counter()

        try:
            response = requests.get(
                url,
                headers=cabecalhos,
                params=params,
                proxies=proxy_dict,
                timeout=timeout_tupla,
            )
            latencia_req = time.perf_counter() - inicio_req

            if response.status_code == 200:
                if _is_valid_target_payload(response.text):
                    rotator.report_success(proxy_url, latencia_req)
                    return response

                ultimo_erro = "Payload interceptado por proxy (Captive/Squid/Block)"
                rotator.report_failure(
                    proxy_url,
                    status_code=403,
                    motivo=ultimo_erro,
                    is_critical_timeout=True,
                )
                continue

            ultimo_erro = f"Status {response.status_code}"
            logger.debug(f"[HTTP] Status {response.status_code} via {proxy_url} para {url}")

            eh_bloqueio_severo = response.status_code in {401, 403, 407, 429, 500, 502, 503, 504, 999}
            rotator.report_failure(
                proxy_url,
                status_code=response.status_code,
                motivo=f"Status {response.status_code}",
                is_critical_timeout=eh_bloqueio_severo,
            )

        except requests.RequestException as excecao:
            ultimo_erro = excecao.__class__.__name__
            logger.debug(f"[HTTP] Erro de rede ({ultimo_erro}) via {proxy_url} para {url}")
            rotator.report_failure(
                proxy_url,
                status_code=None,
                motivo=ultimo_erro,
                is_critical_timeout=True,
            )

    if fallback_direto:
        direct_response = _executar_requisicao_direta(
            url,
            cabecalhos,
            params,
            timeout=(2.5, max(3.5, float(timeout))),
        )
        if direct_response is not None:
            return direct_response

    logger.debug(f"[HTTP] Falha após {rotacao_atual} rotações de IP para {url}. Último erro: {ultimo_erro}")
    return None
