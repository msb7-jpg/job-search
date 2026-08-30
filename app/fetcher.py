import asyncio
from itertools import cycle

import httpx
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

HEADERS: dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}

class ProxyRotator:
    def __init__(self) -> None:
        self.valid_proxies: list[str] = []
        self._proxy_cycle = None

    def carregar_proxies_free_proxy_list(self) -> list[str]:
        """Raspa os proxies elite do free-proxy-list.net e retorna uma lista de strings."""
        url = "https://free-proxy-list.net"
        proxies: list[str] = []
        try:
            response = requests.get(url, headers=HEADERS, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
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
            print(f"❌ Erro ao raspar free-proxy-list.net: {e}")

        print(f"📥 {len(proxies)} proxies carregados do Free-Proxy-List.")
        return proxies

    def carregar_proxies_proxyscrape(self) -> list[str]:
        """Busca os proxies em formato plain text da API v4 do ProxyScrape."""
        url = "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=text"
        proxies: list[str] = []
        try:
            response = requests.get(url, headers=HEADERS, timeout=5)
            if response.status_code == 200:
                linhas = response.text.splitlines()
                for linha in linhas:
                    linha = linha.strip()
                    if not linha:
                        continue

                    if "://" in linha:
                        _, address = linha.split("://", 1)
                    else:
                        address = linha

                    if ":" in address:
                        proxies.append(f"http://{address}")
        except requests.RequestException as e:
            print(f"❌ Erro ao buscar proxies do ProxyScrape: {e}")

        print(f"📥 {len(proxies)} proxies carregados do ProxyScrape API.")
        return proxies

    def carregar_todos_os_proxies(self) -> list[str]:
        """Agrega todas as fontes e remove duplicatas usando um set."""
        brutos_fpl = self.carregar_proxies_free_proxy_list()
        brutos_ps = self.carregar_proxies_proxyscrape()

        # Deduplicação nativa usando set de strings
        unicos = set(brutos_fpl + brutos_ps)
        lista_final = list(unicos)
        print(f"🔗 Total após deduplicação: {len(lista_final)} proxies únicos.")
        return lista_final

    async def _testar_proxy_async(
        self, proxy_str: str, semaphore: asyncio.Semaphore, pbar: tqdm
    ) -> str | None:
        """Testa o proxy contra um endpoint HTTPS real e restrito."""
        async with semaphore:
            try:
                proxy_url = httpx.URL(proxy_str)
                # Timeout mais realista para validação (2.5s)
                async with httpx.AsyncClient(
                    proxy=proxy_url,
                    follow_redirects=True,
                    verify=False,  # Ignora erros de certificado SSL de proxies intermediários
                    timeout=2.5
                ) as client:
                    # Testa contra o próprio SearXNG ou um target HTTPS seguro
                    response = await client.get("https://1.1.1.1/cdn-cgi/trace")
                    if response.status_code == 200 and "ip=" in response.text:
                        return proxy_str
            except (httpx.RequestError, httpx.TimeoutException):
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
        """Valida os proxies unificados de forma assíncrona e monta o ciclo."""
        proxies_brutos = self.carregar_todos_os_proxies()

        self.valid_proxies = asyncio.run(self._validar_em_lote(proxies_brutos, max_concurrency))
        print(f"✅ {len(self.valid_proxies)} proxies válidos prontos para uso.")

        if self.valid_proxies:
            self._proxy_cycle = cycle(self.valid_proxies)
        else:
            print("⚠️ Nenhum proxy válido encontrado.")

    def obter_proximo_proxy(self) -> dict[str, str] | None:
        """Retorna o próximo proxy no formato de dicionário compatível com o requests."""
        if self._proxy_cycle:
            p_str = next(self._proxy_cycle)
            return {"http": p_str, "https": p_str}
        return None


# Instância global do rotacionador
rotator = ProxyRotator()

def requisicao_com_rotacao(
    url: str,
    headers: dict[str, str] | None = None,
    params: dict[str, str] | None = None,
    max_retries: int = 5,
    timeout: int = 5
) -> requests.Response | None:
    headers = headers or HEADERS

    for tentativa in range(1, max_retries + 1):
        # Na última tentativa, faz fallback sem proxy se houver proxies válidos falhando
        if tentativa == max_retries and rotator.valid_proxies:
            print(f"🌐 [Tentativa {tentativa}/{max_retries}] FALLBACK: Tentando sem proxy...")
            proxy = None
        else:
            proxy = rotator.obter_proximo_proxy()

        try:
            proxy_str = proxy['http'] if proxy else 'Sem Proxy'
            print(f"🌐 [Tentativa {tentativa}/{max_retries}] USANDO PROXY: {proxy_str}")
            response = requests.get(url, headers=headers, params=params, proxies=proxy, timeout=timeout)

            if response.status_code == 200:
                return response

            print(f"⚠️ Status {response.status_code}. Alternando proxy...")

        except requests.RequestException:
            print("⚠️ Timeout/Offline. Alternando proxy...")

    print("❌ Todas as tentativas falharam.")
    return None

if __name__ == "__main__":
    rotator.inicializar_pool(max_concurrency=200)

    if rotator.valid_proxies:
        url_alvo = "https://httpbin.org/ip"

        print("\n--- Teste de Requisição ---")
        resposta = requisicao_com_rotacao(url_alvo, max_retries=5)

        if resposta:
            print("✅ Sucesso!")
            print("IP recebido:", resposta.json())
