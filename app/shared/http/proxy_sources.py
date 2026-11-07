import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

from app.core.logging import logger

DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"),
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}

IP_PORT_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}:\d{2,5}\b")

# Endpoints canários rápidos e de alta disponibilidade (TLS + verificação semântica)
CANARY_TARGETS: tuple[dict[str, str], ...] = (
    {
        "url": "https://www.linkedin.com/robots.txt",
        "expected_marker": "user-agent",
    },
    {
        "url": "https://api.ipify.org?format=json",
        "expected_marker": "ip",
    },
    {
        "url": "https://httpbin.org/ip",
        "expected_marker": "origin",
    },
)

INVALID_PROXY_BODY_MARKERS: tuple[str, ...] = (
    "mikrotik",
    "squid",
    "access denied",
    "403 forbidden",
    "proxy error",
    "captive portal",
    "authentication required",
    "attention required! | cloudflare",
)


def sanitizar_esquema_proxy(raw_proxy: str) -> str | None:
    """Garante formato estrito http://ip:porta ou socks5://ip:porta."""
    cleaned = (raw_proxy or "").strip()
    if not cleaned:
        return None
    if cleaned.startswith(("http://", "https://", "socks5://", "socks4://")):
        # Normaliza https:// de proxy HTTP para http:// para evitar erro de túnel TLS duplo no httpx/requests
        if cleaned.startswith("https://"):
            cleaned = "http://" + cleaned[len("https://") :]
        match = IP_PORT_PATTERN.search(cleaned)
        if match:
            scheme = cleaned.split("://")[0]
            return f"{scheme}://{match.group(0)}"
        return None

    match = IP_PORT_PATTERN.search(cleaned)
    if match:
        return f"http://{match.group(0)}"
    return None


def _extrair_ip_portas(texto: str) -> list[str]:
    encontrados = IP_PORT_PATTERN.findall(texto or "")
    sanitizados: list[str] = []
    for item in encontrados:
        normalizado = sanitizar_esquema_proxy(item)
        if normalizado:
            sanitizados.append(normalizado)
    return sanitizados


def validar_integridade_semantica_resposta(body_text: str, expected_marker: str | None = None) -> bool:
    """
    Verifica se a resposta do proxy não é um HTML de interceptação (Squid, MikroTik, Captive Portal)
    e se contém a assinatura semântica esperada.
    """
    corpo_minusculo = (body_text or "").strip().lower()
    if not corpo_minusculo:
        return False

    for invalid_marker in INVALID_PROXY_BODY_MARKERS:
        if invalid_marker in corpo_minusculo:
            return False

    if expected_marker:
        return expected_marker.lower() in corpo_minusculo

    return "origin" in corpo_minusculo or "ip" in corpo_minusculo or "user-agent" in corpo_minusculo


class ProxySourcesCollector:
    """Coletor concorrente e modular de múltiplas fontes públicas de proxies com rastreio de origem."""

    @classmethod
    def coletar_geonode(cls, timeout: int = 4) -> list[str]:
        url = "https://proxylist.geonode.com/api/proxy-list?page=1&limit=500&sort_by=responseTime&sort_type=asc"
        proxies: list[str] = []
        try:
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
            if response.status_code == 200:
                data = response.json()
                for item in data.get("data", []):
                    ip_address = item.get("ip")
                    port_number = item.get("port")
                    protocols = item.get("protocols") or ["http"]
                    if ip_address and port_number:
                        scheme = "socks5" if "socks5" in protocols and "http" not in protocols else "http"
                        sanitized = sanitizar_esquema_proxy(f"{scheme}://{ip_address}:{port_number}")
                        if sanitized:
                            proxies.append(sanitized)
        except Exception as error:
            logger.debug(f"[PROXY-SOURCE] Falha ao consultar Geonode API: {error}")

        logger.debug(f"[PROXY-SOURCE] Geonode retornou {len(proxies)} proxies.")
        return proxies

    @classmethod
    def coletar_github_thespeedx(cls, timeout: int = 4) -> list[str]:
        url = "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt"
        try:
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
            if response.status_code == 200:
                proxies = _extrair_ip_portas(response.text)
                logger.debug(f"[PROXY-SOURCE] TheSpeedX retornou {len(proxies)} proxies.")
                return proxies
        except Exception as error:
            logger.debug(f"[PROXY-SOURCE] Falha ao consultar GitHub TheSpeedX: {error}")
        return []

    @classmethod
    def coletar_github_monosans(cls, timeout: int = 4) -> list[str]:
        url = "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt"
        try:
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
            if response.status_code == 200:
                proxies = _extrair_ip_portas(response.text)
                logger.debug(f"[PROXY-SOURCE] monosans retornou {len(proxies)} proxies.")
                return proxies
        except Exception as error:
            logger.debug(f"[PROXY-SOURCE] Falha ao consultar GitHub monosans: {error}")
        return []

    @classmethod
    def coletar_free_proxy_list(cls, timeout: int = 4) -> list[str]:
        url = "https://free-proxy-list.net"
        proxies: list[str] = []
        try:
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                table = soup.find("table", class_="table-striped")
                if table:
                    for row in table.find_all("tr")[1:]:
                        cols = row.find_all("td")
                        if len(cols) >= 2:
                            ip_address = cols[0].text.strip()
                            port_number = cols[1].text.strip()
                            if ip_address and port_number.isdigit():
                                sanitized = sanitizar_esquema_proxy(f"http://{ip_address}:{port_number}")
                                if sanitized:
                                    proxies.append(sanitized)
        except Exception as error:
            logger.debug(f"[PROXY-SOURCE] Falha ao raspar free-proxy-list.net: {error}")

        logger.debug(f"[PROXY-SOURCE] Free-Proxy-List retornou {len(proxies)} proxies.")
        return proxies

    @classmethod
    def coletar_proxyscrape(cls, timeout: int = 4) -> list[str]:
        url = (
            "https://api.proxyscrape.com/v4/free-proxy-list/get"
            "?request=display_proxies&proxy_format=protocolipport&format=text&timeout=3000"
        )
        try:
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
            if response.status_code == 200:
                proxies = _extrair_ip_portas(response.text)
                logger.debug(f"[PROXY-SOURCE] ProxyScrape retornou {len(proxies)} proxies.")
                return proxies
        except Exception as error:
            logger.debug(f"[PROXY-SOURCE] Falha ao consultar ProxyScrape: {error}")
        return []

    @classmethod
    def coletar_spys_one(cls, timeout: int = 4) -> list[str]:
        url = "https://spys.one/en/https-ssl-proxy/"
        try:
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
            if response.status_code == 200:
                proxies = _extrair_ip_portas(response.text)
                logger.debug(f"[PROXY-SOURCE] Spys.one retornou {len(proxies)} proxies.")
                return proxies
        except Exception as error:
            logger.debug(f"[PROXY-SOURCE] Falha ao raspar spys.one: {error}")
        return []

    @classmethod
    def coletar_todas_as_fontes_com_origem(cls) -> list[tuple[str, str]]:
        """
        Coleta todas as fontes públicas em paralelo (ThreadPool) e retorna tuplas (proxy_url, nome_da_fonte)
        deduplicadas preservando a primeira fonte que forneceu o nó.
        """
        fontes_configuradas = [
            ("geonode", cls.coletar_geonode),
            ("free_proxy_list", cls.coletar_free_proxy_list),
            ("proxyscrape", cls.coletar_proxyscrape),
            ("monosans", cls.coletar_github_monosans),
            ("spys_one", cls.coletar_spys_one),
            ("thespeedx", cls.coletar_github_thespeedx),
        ]

        resultados_por_fonte: dict[str, list[str]] = {}
        with ThreadPoolExecutor(max_workers=len(fontes_configuradas)) as executor:
            futuro_para_fonte = {executor.submit(funcao_coletora): nome_fonte for nome_fonte, funcao_coletora in fontes_configuradas}
            for futuro in as_completed(futuro_para_fonte):
                nome_fonte = futuro_para_fonte[futuro]
                try:
                    lista_proxies = futuro.result()
                    resultados_por_fonte[nome_fonte] = lista_proxies
                except Exception as error:
                    logger.debug(f"[PROXY-SOURCE] Erro inesperado na fonte {nome_fonte}: {error}")
                    resultados_por_fonte[nome_fonte] = []

        # Ordem de prioridade orientada a dados (fontes mais frescas e filtradas primeiro)
        vistos: set[str] = set()
        candidatos_com_origem: list[tuple[str, str]] = []
        for nome_fonte, _ in fontes_configuradas:
            for proxy_url in resultados_por_fonte.get(nome_fonte, []):
                if proxy_url not in vistos:
                    vistos.add(proxy_url)
                    candidatos_com_origem.append((proxy_url, nome_fonte))

        logger.info(f"🌐 [PROXY-SOURCES] Total de candidatos únicos coletados: {len(candidatos_com_origem)}")
        return candidatos_com_origem

    @classmethod
    def coletar_todas_as_fontes(cls) -> list[str]:
        """Retorna lista simples de URLs de proxies únicos (compatibilidade)."""
        com_origem = cls.coletar_todas_as_fontes_com_origem()
        return [proxy_url for proxy_url, _ in com_origem]
