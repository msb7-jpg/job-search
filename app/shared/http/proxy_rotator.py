import asyncio
import threading
from collections import deque

import httpx
import requests
from tqdm import tqdm

from app.core.logging import logger
from app.shared.http.proxy_sources import DEFAULT_HEADERS, ProxySourcesCollector


class ProxyRotator:
    """Gerenciador dinâmico e thread-safe de pool de proxies com validação em lote e auto-reabastecimento."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.valid_proxies: deque[str] = deque()
        self.dead_proxies: set[str] = set()
        self.tested_proxies: set[str] = set()
        self._pool_initialized = False

    @property
    def total_valid(self) -> int:
        with self._lock:
            return len(self.valid_proxies)

    def carregar_novos_candidatos(self) -> list[str]:
        """Coleta proxies de todas as fontes públicas ignorando os já testados."""
        candidatos = ProxySourcesCollector.coletar_todas_as_fontes()
        with self._lock:
            novos = [p for p in candidatos if p not in self.tested_proxies]
            self.tested_proxies.update(novos)
        logger.info(f"🔍 [PROXY-ROTATOR] Total de novos candidatos encontrados para teste: {len(novos)}")
        return novos

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
            with tqdm(total=len(proxies_brutos), desc="🔍 Validando Proxies", unit="proxy") as pbar:
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
        max_concurrency: int = 250,
        strategy: object = None,
    ) -> None:
        """Inicializa o pool com validação em lote assíncrona."""
        with self._lock:
            if self._pool_initialized and len(self.valid_proxies) > 0:
                return
            self._pool_initialized = True

        logger.info("🚀 [PROXY-ROTATOR] Inicializando Pool de Proxies com validação em lote...")
        candidatos = self.carregar_novos_candidatos()
        if not candidatos:
            logger.warning("[PROXY-ROTATOR] Nenhum candidato carregado das fontes.")
            return

        validos = asyncio.run(
            self._validar_em_lote(candidatos, max_concurrency=max_concurrency, timeout=2.5, mostrar_progresso=True)
        )
        with self._lock:
            self.valid_proxies = deque(validos)
            falhados = set(candidatos) - set(validos)
            self.dead_proxies.update(falhados)

        logger.info(f"✅ [PROXY-ROTATOR] {len(self.valid_proxies)} proxies válidos prontos no pool inicial.")

    def reabastecer_pool_se_vazio(self, max_concurrency: int = 250) -> None:
        """Recarrega novas fontes e valida um novo lote quando o pool de proxies válidos se esgotar."""
        with self._lock:
            if len(self.valid_proxies) > 0:
                return

        logger.warning("⚠️ [PROXY-ROTATOR] Pool de proxies esgotado! Iniciando recarregamento e nova validação em lote...")

        candidatos = self.carregar_novos_candidatos()

        # Se não houver novos candidatos não testados, resetamos para permitir nova tentativa nas fontes
        if not candidatos:
            logger.info("🔄 [PROXY-ROTATOR] Reiniciando ciclo de candidatos para fontes públicas...")
            with self._lock:
                self.tested_proxies.clear()
            candidatos = self.carregar_novos_candidatos()

        if not candidatos:
            logger.error("❌ [PROXY-ROTATOR] Não foi possível encontrar proxies adicionais nas fontes públicas.")
            return

        novos_validos = asyncio.run(
            self._validar_em_lote(candidatos, max_concurrency=max_concurrency, timeout=2.5, mostrar_progresso=True)
        )
        with self._lock:
            self.valid_proxies = deque(novos_validos)
            falhados = set(candidatos) - set(novos_validos)
            self.dead_proxies.update(falhados)

        logger.info(f"✅ [PROXY-ROTATOR] Pool recarregado com {len(self.valid_proxies)} proxies saudáveis.")

    def remover_proxy_invalido(self, proxy_str: str, motivo: str = "falha") -> None:
        """Remove o proxy com falha (429, timeout, erro de rede) instantaneamente do pool ativo."""
        with self._lock:
            if proxy_str in self.valid_proxies:
                self.valid_proxies.remove(proxy_str)
                self.dead_proxies.add(proxy_str)
                total_restante = len(self.valid_proxies)
                logger.warning(
                    f"🗑️ [PROXY-ROTATOR] Proxy descartado ({motivo}): {proxy_str} | Restantes no pool: {total_restante}"
                )

    def adicionar_proxy_valido(self, proxy_str: str) -> None:
        """Adiciona ou revalida um proxy no pool."""
        with self._lock:
            if proxy_str not in self.valid_proxies:
                self.valid_proxies.append(proxy_str)
                self.dead_proxies.discard(proxy_str)

    def obter_proximo_proxy(self) -> dict[str, str] | None:
        """Obtém o próximo proxy do pool aplicando rotação circular (Round-Robin)."""
        proxy_str = self.obter_proxima_string_proxy()
        if proxy_str:
            return {"http": proxy_str, "https": proxy_str}
        return None

    def obter_proxima_string_proxy(self) -> str | None:
        """Obtém a próxima string de proxy com rotação segura. Se o pool estiver vazio, tenta recarregar."""
        if self.total_valid == 0:
            self.reabastecer_pool_se_vazio()

        with self._lock:
            if not self.valid_proxies:
                return None

            proxy_selecionado = self.valid_proxies[0]
            self.valid_proxies.rotate(-1)
            return proxy_selecionado


rotator = ProxyRotator()
