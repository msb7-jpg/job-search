import asyncio
import threading
import time
from collections import deque

import httpx
import requests
from tqdm import tqdm

from app.core.logging import logger
from app.models.enums import ProxyStrategyEnum
from app.shared.http.proxy_sources import DEFAULT_HEADERS, ProxySourcesCollector


class ProxyRotator:
    """Gerenciador dinâmico e thread-safe de pool e rotação de proxies com múltiplas estratégias."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.valid_proxies: deque[str] = deque()
        self.untested_proxies: deque[str] = deque()
        self.dead_proxies: set[str] = set()
        self._pool_initialized = False
        self._background_thread: threading.Thread | None = None
        self._stop_background_event = threading.Event()
        self.strategy: ProxyStrategyEnum = ProxyStrategyEnum.ADAPTIVE_FAILOVER

    @property
    def total_valid(self) -> int:
        with self._lock:
            return len(self.valid_proxies)

    def carregar_todos_os_proxies(self) -> list[str]:
        candidatos = ProxySourcesCollector.coletar_todas_as_fontes()
        with self._lock:
            novos = [p for p in candidatos if p not in self.dead_proxies and p not in self.valid_proxies]
            self.untested_proxies.extend(novos)
        logger.info(f"🔍 [PROXY-ROTATOR] Total de novos candidatos prontos para teste: {len(novos)}")
        return list(novos)

    @staticmethod
    async def _testar_proxy_async(
        proxy_str: str, semaphore: asyncio.Semaphore, pbar: tqdm | None = None, timeout: float = 2.5
    ) -> str | None:
        async with semaphore:
            try:
                proxy_url = httpx.URL(proxy_str)
                async with httpx.AsyncClient(
                    proxy=proxy_url,
                    follow_redirects=True,
                    verify=False,  # noqa: S501
                    timeout=timeout,
                ) as client:
                    response = await client.get(
                        "https://httpbin.org/ip",
                        headers={"User-Agent": DEFAULT_HEADERS["User-Agent"]},
                    )
                    if response.status_code == 200:
                        body = str(response.text or "").lower()
                        if "origin" in body or "ip" in body:
                            return proxy_str
            except (httpx.RequestError, httpx.TimeoutException, ValueError, Exception):
                pass
            finally:
                if pbar is not None:
                    pbar.update(1)
            return None

    @classmethod
    def testar_proxy_sincrono(cls, proxy_str: str, timeout: float = 2.0) -> bool:
        try:
            response = requests.get(
                "https://httpbin.org/ip",
                proxies={"http": proxy_str, "https": proxy_str},
                headers=DEFAULT_HEADERS,
                timeout=timeout,
            )
            if response.status_code == 200 and ("origin" in response.text.lower() or "ip" in response.text.lower()):
                return True
        except Exception:
            return False
        return False

    async def _validar_em_lote(
        self, proxies_brutos: list[str], max_concurrency: int, timeout: float = 2.5, mostrar_progresso: bool = True
    ) -> list[str]:
        if not proxies_brutos:
            return []
        semaphore = asyncio.Semaphore(max_concurrency)
        if mostrar_progresso:
            with tqdm(total=len(proxies_brutos), desc="🔍 Testando Proxies", unit="proxy") as pbar:
                tarefas = [
                    self._testar_proxy_async(proxy_str, semaphore, pbar, timeout=timeout)
                    for proxy_str in proxies_brutos
                ]
                resultados = await asyncio.gather(*tarefas)
        else:
            tarefas = [
                self._testar_proxy_async(proxy_str, semaphore, None, timeout=timeout)
                for proxy_str in proxies_brutos
            ]
            resultados = await asyncio.gather(*tarefas)

        return [p for p in resultados if p is not None]

    def inicializar_pool(
        self,
        max_concurrency: int = 200,
        strategy: ProxyStrategyEnum = ProxyStrategyEnum.ADAPTIVE_FAILOVER,
    ) -> None:
        if self._pool_initialized:
            return
        self._pool_initialized = True
        self.strategy = strategy

        logger.info(f"🚀 [PROXY-ROTATOR] Inicializando Pool de Proxies com estratégia: {self.strategy.value}")
        candidatos = self.carregar_todos_os_proxies()
        if not candidatos:
            logger.warning("[PROXY-ROTATOR] Nenhum candidato carregado das fontes.")
            return

        validos = asyncio.run(self._validar_em_lote(candidatos, max_concurrency=max_concurrency, timeout=2.5, mostrar_progresso=True))
        with self._lock:
            self.valid_proxies = deque(validos)
            # Marcar os que falharam
            falhados = set(candidatos) - set(validos)
            self.dead_proxies.update(falhados)

        logger.info(f"✅ [PROXY-ROTATOR] {len(self.valid_proxies)} proxies válidos prontos no pool inicial.")

        if self.strategy == ProxyStrategyEnum.BACKGROUND_POOL:
            self.iniciar_background_refresh()

    def remover_proxy_invalido(self, proxy_str: str) -> None:
        """Remove o proxy com falha instantaneamente do pool."""
        with self._lock:
            if proxy_str in self.valid_proxies:
                self.valid_proxies.remove(proxy_str)
                self.dead_proxies.add(proxy_str)
                logger.debug(f"🗑️ [PROXY-ROTATOR] Proxy descartado: {proxy_str} | Restantes: {len(self.valid_proxies)}")

    def adicionar_proxy_valido(self, proxy_str: str) -> None:
        """Adiciona ou revalida um proxy no pool."""
        with self._lock:
            if proxy_str not in self.valid_proxies:
                self.valid_proxies.append(proxy_str)
                self.dead_proxies.discard(proxy_str)

    def obter_proximo_proxy(self) -> dict[str, str] | None:
        """Obtém o próximo proxy aplicando a estratégia ativa (com failover/pre-flight se configurado)."""
        proxy_str = self.obter_proxima_string_proxy()
        if proxy_str:
            return {"http": proxy_str, "https": proxy_str}
        return None

    def obter_proxima_string_proxy(self) -> str | None:
        """Obtém a próxima string de proxy com rotação segura e validação Just-In-Time se PRE_FLIGHT estiver ativo."""
        with self._lock:
            if not self.valid_proxies:
                # Tentar reabastecer a partir de untested_proxies se houver
                if self.untested_proxies:
                    candidato = self.untested_proxies.popleft()
                    if self.testar_proxy_sincrono(candidato, timeout=1.5):
                        self.valid_proxies.append(candidato)
                        return candidato
                    self.dead_proxies.add(candidato)
                return None

            if self.strategy == ProxyStrategyEnum.PRE_FLIGHT:
                while self.valid_proxies:
                    proxy_candidato = self.valid_proxies.popleft()
                    if self.testar_proxy_sincrono(proxy_candidato, timeout=1.5):
                        self.valid_proxies.append(proxy_candidato)
                        return proxy_candidato
                    self.dead_proxies.add(proxy_candidato)
                    logger.debug(f"[PRE-FLIGHT] Proxy {proxy_candidato} falhou no teste prévio e foi descartado.")
                return None

            # Estratégia padrão / ADAPTIVE_FAILOVER & BACKGROUND_POOL: Rotação circular direta
            proxy_selecionado = self.valid_proxies[0]
            self.valid_proxies.rotate(-1)
            return proxy_selecionado

    def reabastecer_pool_background(self, max_concurrency: int = 100) -> None:
        """Coleta novas fontes e valida candidatos não testados."""
        with self._lock:
            precisa_coleta = len(self.untested_proxies) < 50
        if precisa_coleta:
            self.carregar_todos_os_proxies()

        with self._lock:
            lote_teste = [self.untested_proxies.popleft() for _ in range(min(150, len(self.untested_proxies)))]

        if lote_teste:
            logger.debug(f"[PROXY-ROTATOR] Validando lote em background com {len(lote_teste)} candidatos...")
            novos_validos = asyncio.run(
                self._validar_em_lote(lote_teste, max_concurrency=max_concurrency, timeout=2.0, mostrar_progresso=False)
            )
            with self._lock:
                for valido in novos_validos:
                    if valido not in self.valid_proxies:
                        self.valid_proxies.append(valido)
                mortos = set(lote_teste) - set(novos_validos)
                self.dead_proxies.update(mortos)
            logger.info(f"🔄 [PROXY-BACKGROUND] +{len(novos_validos)} proxies válidos adicionados ao pool (Total: {len(self.valid_proxies)})")

    def iniciar_background_refresh(self, intervalo_segundos: int = 45) -> None:
        """Inicia thread daemon de verificação contínua e reabastecimento."""
        if self._background_thread and self._background_thread.is_alive():
            return

        self._stop_background_event.clear()

        def _loop() -> None:
            logger.info("🛰️ [PROXY-BACKGROUND] Thread de verificação contínua iniciada.")
            while not self._stop_background_event.is_set():
                try:
                    self.reabastecer_pool_background()
                except Exception as erro:
                    logger.debug(f"[PROXY-BACKGROUND] Erro no ciclo de background: {erro}")
                time.sleep(intervalo_segundos)

        self._background_thread = threading.Thread(target=_loop, daemon=True, name="ProxyBackgroundRefresher")
        self._background_thread.start()

    def parar_background_refresh(self) -> None:
        if self._background_thread and self._background_thread.is_alive():
            self._stop_background_event.set()
            self._background_thread.join(timeout=2.0)


rotator = ProxyRotator()
