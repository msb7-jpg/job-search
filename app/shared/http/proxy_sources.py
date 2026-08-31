import re

import requests
from bs4 import BeautifulSoup

from app.core.logging import logger

DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}

IP_PORT_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}:\d{2,5}\b")


def _extrair_ip_portas(texto: str) -> list[str]:
    encontrados = IP_PORT_PATTERN.findall(texto or "")
    return [f"http://{item}" for item in encontrados]


class ProxySourcesCollector:
    """Coletor modular de múltiplas fontes públicas de proxies."""

    @classmethod
    def coletar_geonode(cls, timeout: int = 6) -> list[str]:
        url = "https://proxylist.geonode.com/api/proxy-list?page=1&limit=500&sort_by=responseTime&sort_type=asc"
        proxies: list[str] = []
        try:
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
            if response.status_code == 200:
                data = response.json()
                for item in data.get("data", []):
                    ip = item.get("ip")
                    port = item.get("port")
                    if ip and port:
                        proxies.append(f"http://{ip}:{port}")
        except Exception as error:
            logger.debug(f"[PROXY-SOURCE] Falha ao consultar Geonode API: {error}")

        logger.debug(f"[PROXY-SOURCE] Geonode retornou {len(proxies)} proxies.")
        return proxies

    @classmethod
    def coletar_github_thespeedx(cls, timeout: int = 6) -> list[str]:
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
    def coletar_github_monosans(cls, timeout: int = 6) -> list[str]:
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
    def coletar_free_proxy_list(cls, timeout: int = 6) -> list[str]:
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
                            ip = cols[0].text.strip()
                            port = cols[1].text.strip()
                            if ip and port.isdigit():
                                proxies.append(f"http://{ip}:{port}")
        except Exception as error:
            logger.debug(f"[PROXY-SOURCE] Falha ao raspar free-proxy-list.net: {error}")

        logger.debug(f"[PROXY-SOURCE] Free-Proxy-List retornou {len(proxies)} proxies.")
        return proxies

    @classmethod
    def coletar_proxyscrape(cls, timeout: int = 6) -> list[str]:
        url = "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=text"
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
    def coletar_spys_one(cls, timeout: int = 6) -> list[str]:
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
    def coletar_todas_as_fontes(cls) -> list[str]:
        todos: list[str] = []
        todos.extend(cls.coletar_geonode())
        todos.extend(cls.coletar_github_monosans())
        todos.extend(cls.coletar_github_thespeedx())
        todos.extend(cls.coletar_free_proxy_list())
        todos.extend(cls.coletar_proxyscrape())
        todos.extend(cls.coletar_spys_one())

        unicos = list(dict.fromkeys(todos))
        logger.info(f"🌐 [PROXY-SOURCES] Total de candidatos únicos coletados: {len(unicos)}")
        return unicos
