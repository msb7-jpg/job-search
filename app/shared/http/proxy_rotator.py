import asyncio
from itertools import cycle

import httpx
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from app.core.logging import logger

DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}

class ProxyRotator:
    def __init__(self) -> None:
        self.valid_proxies: list[str] = []
        self._proxy_cycle = None
        self._pool_initialized = False

    @staticmethod
    def _proxy_response_looks_valid(response: requests.Response) -> bool:
        if response is None:
            return False
        try:
            status = int(response.status_code)
        except (TypeError, ValueError):
            return False

        if status != 200:
            return False

        content_type = str(response.headers.get("Content-Type", "")).lower()
        body = str(response.text or "").lower()

        if "text/html" in content_type or "<html" in body or "<body" in body:
            return False

        return any(marker in body for marker in ("origin", "ip", "client_ip", "remote_addr"))

    def carregar_proxies_free_proxy_list(self) -> list[str]:
        url = "https://free-proxy-list.net"
        proxies: list[str] = []
        try:
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=5)
            soup = BeautifulSoup(response.text, "html.parser")
            table = soup.find("table", class_="table-striped")
            if not table:
                return proxies

            for row in table.find_all("tr")[1:]:
                cols = row.find_all("td")
                if len(cols) >= 5 and cols[4].text.strip() == "elite proxy":
                    ip = cols[0].text.strip()
                    port = cols[1].text.strip()
                    proxies.append(f"http://{ip}:{port}")
        except requests.RequestException as e:
            logger.warning(f"Erro ao raspar free-proxy-list.net: {e}")

        logger.debug(f"{len(proxies)} proxies carregados do Free-Proxy-List.")
        return proxies

    def carregar_proxies_proxyscrape(self) -> list[str]:
        url = "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=text"
        proxies: list[str] = []
        try:
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=5)
            if response.status_code == 200:
                for linha_bruta in response.text.splitlines():
                    linha = linha_bruta.strip()
                    if not linha:
                        continue
                    address = linha.split("://", 1)[1] if "://" in linha else linha
                    if ":" in address:
                        proxies.append(f"http://{address}")
        except requests.RequestException as e:
            logger.warning(f"Erro ao buscar proxies do ProxyScrape: {e}")

        logger.debug(f"{len(proxies)} proxies carregados do ProxyScrape API.")
        return proxies

    def carregar_todos_os_proxies(self) -> list[str]:
        brutos_fpl = self.carregar_proxies_free_proxy_list()
        brutos_ps = self.carregar_proxies_proxyscrape()
        unicos = list(set(brutos_fpl + brutos_ps))
        logger.info(f"Total de proxies únicos descobertos para teste: {len(unicos)}")
        return unicos

    async def _testar_proxy_async(
        self, proxy_str: str, semaphore: asyncio.Semaphore, pbar: tqdm
    ) -> str | None:
        async with semaphore:
            try:
                proxy_url = httpx.URL(proxy_str)
                async with httpx.AsyncClient(
                    proxy=proxy_url,
                    follow_redirects=True,
                    verify=False,  # noqa: S501
                    timeout=3.0,
                ) as client:
                    response = await client.get("https://httpbin.org/ip", headers={"User-Agent": DEFAULT_HEADERS["User-Agent"]})
                    if response.status_code == 200:
                        body = str(response.text or "").lower()
                        if "origin" in body or "ip" in body:
                            return proxy_str
            except (httpx.RequestError, httpx.TimeoutException, ValueError):
                pass
            finally:
                pbar.update(1)
            return None

    async def _validar_em_lote(self, proxies_brutos: list[str], max_concurrency: int) -> list[str]:
        semaphore = asyncio.Semaphore(max_concurrency)
        with tqdm(total=len(proxies_brutos), desc="🔍 Testando Proxies", unit="proxy") as pbar:
            tarefas = [
                self._testar_proxy_async(proxy_str, semaphore, pbar)
                for proxy_str in proxies_brutos
            ]
            resultados = await asyncio.gather(*tarefas)
        return [p for p in resultados if p is not None]

    def inicializar_pool(self, max_concurrency: int = 200) -> None:
        if self._pool_initialized:
            return
        self._pool_initialized = True
        proxies_brutos = self.carregar_todos_os_proxies()
        if not proxies_brutos:
            logger.warning("Nenhum proxy bruto carregado; continuando sem proxies.")
            self.valid_proxies = []
            self._proxy_cycle = None
            return

        self.valid_proxies = asyncio.run(self._validar_em_lote(proxies_brutos, max_concurrency))
        logger.info(f"✅ {len(self.valid_proxies)} proxies válidos prontos no pool.")
        if self.valid_proxies:
            self._proxy_cycle = cycle(self.valid_proxies)
        else:
            logger.warning("Nenhum proxy válido encontrado; executando em modo direto.")
            self._proxy_cycle = None

    def obter_proximo_proxy(self) -> dict[str, str] | None:
        if self._proxy_cycle:
            p_str = next(self._proxy_cycle)
            return {"http": p_str, "https": p_str}
        return None

    def obter_proxima_string_proxy(self) -> str | None:
        if self._proxy_cycle:
            return next(self._proxy_cycle)
        return None


rotator = ProxyRotator()
