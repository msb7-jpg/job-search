import asyncio
import json
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any

import httpx
import requests
from tqdm import tqdm

from app.core.config import DATA_DIR
from app.core.logging import logger
from app.shared.http.proxy_record import ProxyRecord
from app.shared.http.proxy_sources import (
    DEFAULT_HEADERS,
    ProxySourcesCollector,
    sanitizar_esquema_proxy,
    validar_integridade_semantica_resposta,
)


class RealtimeProxyRotator:
    """
    Gerenciador Produtor-Consumidor Reativo de Proxies com Fila de Prioridade (EWMA),
    controle de concorrência por nó (in_flight), Circuit Breaker inline e Cache Tier-A.
    """

    MIN_READY_THRESHOLD: int = 12
    CONNECT_TIMEOUT: float = 2.0
    READ_TIMEOUT: float = 2.8
    NODE_TTL_SECONDS: float = 600.0
    TIER_A_TTL_SECONDS: float = 1800.0

    def __init__(self, tier_a_cache_path: Path | None = None) -> None:
        self._lock = threading.RLock()
        self._replenish_lock = threading.Lock()
        self._is_replenishing = False

        # Estruturas reativas em memória
        self._records: dict[str, ProxyRecord] = {}
        self.valid_proxies: deque[str] = deque()
        self.dead_proxies: set[str] = set()
        self.tested_proxies: set[str] = set()
        self.seen_cache: set[str] = set()

        # Telemetria orientada a dados por fonte
        self.source_stats: dict[str, dict[str, int]] = {}
        self._total_scraped: int = 0
        self._total_approved: int = 0
        self._last_telemetry_ts: float = 0.0
        self._pool_initialized: bool = False

        self.tier_a_cache_path: Path = tier_a_cache_path or (DATA_DIR / "proxy_tier_a.json")

    @property
    def total_valid(self) -> int:
        with self._lock:
            self._sync_valid_deque_locked()
            return len(self.valid_proxies)

    def _sync_valid_deque_locked(self) -> None:
        """Sincroniza a deque ordenada por prioridade (menor score EWMA primeiro) e expurga nós expirados."""
        ativos_ordenados: list[ProxyRecord] = []
        expirados: list[str] = []

        for proxy_url, record in list(self._records.items()):
            if not record.is_active or proxy_url in self.dead_proxies:
                expirados.append(proxy_url)
                continue
            if record.is_expired(self.NODE_TTL_SECONDS) and record.in_flight == 0:
                expirados.append(proxy_url)
                continue
            record.calculate_priority()
            ativos_ordenados.append(record)

        for proxy_url in expirados:
            self._records.pop(proxy_url, None)

        ativos_ordenados.sort(key=lambda item: (item.in_flight > 0, item.priority))
        self.valid_proxies = deque(record.url for record in ativos_ordenados)

    def _registrar_estatistica_fonte(self, source: str, aprovados: int = 0, testados: int = 0) -> None:
        with self._lock:
            stats = self.source_stats.setdefault(source, {"testados": 0, "aprovados": 0, "sucessos_reais": 0})
            stats["testados"] += testados
            stats["aprovados"] += aprovados

    def carregar_cache_tier_a(self) -> list[ProxyRecord]:
        """Carrega proxies Tier-A persistidos em disco se estiverem dentro da janela de TTL."""
        if not self.tier_a_cache_path.exists():
            return []
        try:
            raw_text = self.tier_a_cache_path.read_text(encoding="utf-8")
            payload = json.loads(raw_text)
            saved_at = float(payload.get("saved_at", 0.0))
            if (time.time() - saved_at) > self.TIER_A_TTL_SECONDS:
                return []

            records: list[ProxyRecord] = []
            for item in payload.get("proxies", []):
                record = ProxyRecord.from_dict(item)
                if record.url and record.url not in self.dead_proxies:
                    records.append(record)
        except Exception as error:
            logger.debug(f"[PROXY-ROTATOR] Falha ao ler cache Tier-A: {error}")
            return []
        else:
            return records

    def salvar_cache_tier_a(self) -> None:
        """Persiste os melhores nós ativos (Tier-A) para Warm Start em futuras execuções."""
        try:
            with self._lock:
                tier_a_nodes = [
                    record.to_dict() for record in sorted(self._records.values(), key=lambda rec: rec.priority) if record.is_tier_a()
                ][:60]

            if not tier_a_nodes:
                return

            self.tier_a_cache_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "saved_at": time.time(),
                "total": len(tier_a_nodes),
                "proxies": tier_a_nodes,
            }
            self.tier_a_cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception as error:
            logger.debug(f"[PROXY-ROTATOR] Não foi possível salvar cache Tier-A: {error}")

    def carregar_novos_candidatos_com_origem(self) -> list[tuple[str, str]]:
        """Coleta proxies de todas as fontes públicas filtrando pelo seen_cache global."""
        candidatos_brutos = ProxySourcesCollector.coletar_todas_as_fontes_com_origem()
        novos: list[tuple[str, str]] = []
        with self._lock:
            for proxy_raw, source_name in candidatos_brutos:
                sanitizado = sanitizar_esquema_proxy(proxy_raw)
                if not sanitizado:
                    continue
                if sanitizado not in self.seen_cache and sanitizado not in self.tested_proxies:
                    self.seen_cache.add(sanitizado)
                    self.tested_proxies.add(sanitizado)
                    novos.append((sanitizado, source_name))
            self._total_scraped += len(novos)

        logger.info(f"🔍 [PROXY-ROTATOR] Total de novos candidatos inéditos para validação: {len(novos)}")
        return novos

    def carregar_novos_candidatos(self) -> list[str]:
        """Método compatível que retorna apenas a lista de strings de novos candidatos."""
        com_origem = self.carregar_novos_candidatos_com_origem()
        return [proxy_url for proxy_url, _ in com_origem]

    @staticmethod
    async def _testar_proxy_async(
        proxy_str: str,
        semaphore: asyncio.Semaphore,
        pbar: tqdm | None = None,
        timeout: float = 2.5,
        source: str = "public",
    ) -> ProxyRecord | None:
        """
        Pre-flight Validation Pipeline:
        Testa handshake TLS/CONNECT e integridade semântica contra canary rápido com timeout granular agressivo.
        """
        async with semaphore:
            inicio = time.perf_counter()
            try:
                proxy_url = httpx.URL(proxy_str)
                granular_timeout = httpx.Timeout(
                    connect=min(2.0, timeout),
                    read=timeout,
                    write=2.0,
                    pool=2.0,
                )
                limits = httpx.Limits(max_connections=20, max_keepalive_connections=5)
                async with httpx.AsyncClient(
                    proxy=proxy_url,
                    follow_redirects=True,
                    verify=False,  # noqa: S501
                    timeout=granular_timeout,
                    limits=limits,
                ) as client:
                    # Testa túnel HTTPS e integridade semântica do payload
                    response = await client.get(
                        "https://api.ipify.org?format=json",
                        headers={"User-Agent": DEFAULT_HEADERS["User-Agent"]},
                    )
                    latencia = time.perf_counter() - inicio
                    if response.status_code == 200 and latencia <= (timeout + 0.5):
                        body = str(response.text or "")
                        if validar_integridade_semantica_resposta(body, expected_marker="ip"):
                            return ProxyRecord(
                                url=proxy_str,
                                source=source,
                                latency_ewma=round(latencia, 4),
                                total_successes=1,
                            )
            except (httpx.RequestError, httpx.TimeoutException, ValueError, Exception):
                pass
            finally:
                if pbar is not None:
                    pbar.update(1)
            return None

    @classmethod
    def testar_proxy_sincrono(cls, proxy_str: str, timeout: float = 2.0) -> bool:
        """Validação síncrona com verificação de integridade semântica."""
        try:
            response = requests.get(
                "https://httpbin.org/ip",
                proxies={"http": proxy_str, "https": proxy_str},
                headers=DEFAULT_HEADERS,
                timeout=timeout,
            )
            if response.status_code == 200 and validar_integridade_semantica_resposta(response.text):
                return True
        except Exception:
            return False
        return False

    async def _validar_registros_em_lote(
        self,
        candidatos_com_origem: list[tuple[str, str]],
        max_concurrency: int,
        timeout: float = 2.5,
        mostrar_progresso: bool = True,
    ) -> list[ProxyRecord]:
        if not candidatos_com_origem:
            return []

        semaphore = asyncio.Semaphore(max_concurrency)
        if mostrar_progresso:
            with tqdm(total=len(candidatos_com_origem), desc="🔍 Validando Proxies (Pre-Flight TLS)", unit="nó") as pbar:
                tarefas = [
                    self._testar_proxy_async(proxy_str, semaphore, pbar, timeout=timeout, source=source)
                    for proxy_str, source in candidatos_com_origem
                ]
                resultados = await asyncio.gather(*tarefas)
        else:
            tarefas = [
                self._testar_proxy_async(proxy_str, semaphore, None, timeout=timeout, source=source)
                for proxy_str, source in candidatos_com_origem
            ]
            resultados = await asyncio.gather(*tarefas)

        aprovados: list[ProxyRecord] = [registro for registro in resultados if registro is not None]
        aprovados.sort(key=lambda rec: rec.priority)
        return aprovados

    async def _validar_em_lote(
        self,
        proxies_brutos: list[str],
        max_concurrency: int,
        timeout: float = 2.5,
        mostrar_progresso: bool = True,
    ) -> list[str]:
        """Compatibilidade para chamadas que passam lista de strings e esperam lista de strings."""
        pares = [(proxy_str, "batch") for proxy_str in proxies_brutos]
        registros = await self._validar_registros_em_lote(
            pares,
            max_concurrency=max_concurrency,
            timeout=timeout,
            mostrar_progresso=mostrar_progresso,
        )
        return [rec.url for rec in registros]

    def _absorver_registros_aprovados(
        self,
        candidatos_com_origem: list[tuple[str, str]],
        aprovados: list[ProxyRecord],
    ) -> None:
        urls_aprovadas = {rec.url for rec in aprovados}
        with self._lock:
            for _, source_name in candidatos_com_origem:
                self._registrar_estatistica_fonte(source_name, testados=1)

            for record in aprovados:
                existente = self._records.get(record.url)
                if existente:
                    existente.record_success(record.latency_ewma)
                else:
                    self._records[record.url] = record
                self.dead_proxies.discard(record.url)
                self._registrar_estatistica_fonte(record.source, aprovados=1)

            for proxy_url, _ in candidatos_com_origem:
                if proxy_url not in urls_aprovadas and proxy_url not in self._records:
                    self.dead_proxies.add(proxy_url)

            self._total_approved += len(aprovados)
            self._sync_valid_deque_locked()

        self.salvar_cache_tier_a()
        self.emitir_telemetria(forcar=True)

    def inicializar_pool(
        self,
        max_concurrency: int = 250,
        strategy: object = None,
    ) -> None:
        """
        Inicializa o pool reativo:
        1. Tenta Warm Start instantâneo via Cache Tier-A.
        2. Caso o cache esteja frio ou insuficiente, executa Pre-Flight Validation concorrente.
        """
        with self._lock:
            if self._pool_initialized and len(self.valid_proxies) > 0:
                return
            self._pool_initialized = True

        # Etapa 1: Warm Start via Cache Tier-A
        cached_records = self.carregar_cache_tier_a()
        if cached_records:
            logger.info(f"⚡ [PROXY-ROTATOR] Testando Warm Start com {len(cached_records)} proxies Tier-A em cache...")
            pares_cache = [(rec.url, rec.source) for rec in cached_records]
            aprovados_cache = asyncio.run(
                self._validar_registros_em_lote(
                    pares_cache,
                    max_concurrency=min(100, max_concurrency),
                    timeout=2.0,
                    mostrar_progresso=False,
                )
            )
            if aprovados_cache:
                self._absorver_registros_aprovados(pares_cache, aprovados_cache)
                logger.info(f"🚀 [PROXY-ROTATOR] Warm Start concluído! {len(aprovados_cache)} proxies Tier-A prontos imediatamente.")
                if len(aprovados_cache) >= self.MIN_READY_THRESHOLD:
                    # Dispara reabastecimento complementar em background sem travar o início
                    self._disparar_reabastecimento_background(max_concurrency=max_concurrency)
                    return

        # Etapa 2: Coleta e Validação Pre-Flight Completa
        logger.info("🚀 [PROXY-ROTATOR] Inicializando Pool Reativo de Proxies com Pre-Flight TLS...")
        candidatos_com_origem = self.carregar_novos_candidatos_com_origem()
        if not candidatos_com_origem:
            logger.warning("[PROXY-ROTATOR] Nenhum candidato carregado das fontes públicas.")
            return

        aprovados = asyncio.run(
            self._validar_registros_em_lote(
                candidatos_com_origem,
                max_concurrency=max_concurrency,
                timeout=2.5,
                mostrar_progresso=True,
            )
        )
        self._absorver_registros_aprovados(candidatos_com_origem, aprovados)
        logger.info(f"✅ [PROXY-ROTATOR] {self.total_valid} proxies aprovados e ordenados por EWMA no pool inicial.")

    def _disparar_reabastecimento_background(self, max_concurrency: int = 250) -> None:
        """Aciona o Harvester + Validator em uma daemon thread separada sem bloquear os Scraper Workers."""
        if not self._replenish_lock.acquire(blocking=False):
            return

        def _worker() -> None:
            try:
                self._is_replenishing = True
                candidatos = self.carregar_novos_candidatos_com_origem()
                if not candidatos:
                    with self._lock:
                        self.tested_proxies.clear()
                        self.seen_cache.clear()
                    candidatos = self.carregar_novos_candidatos_com_origem()

                if candidatos:
                    aprovados = asyncio.run(
                        self._validar_registros_em_lote(
                            candidatos,
                            max_concurrency=max_concurrency,
                            timeout=2.5,
                            mostrar_progresso=False,
                        )
                    )
                    self._absorver_registros_aprovados(candidatos, aprovados)
                    logger.info(
                        f"🔄 [PROXY-ROTATOR] Reabastecimento em background concluído: +{len(aprovados)} nós (Ativos: {self.total_valid})."
                    )
            except Exception as error:
                logger.debug(f"[PROXY-ROTATOR] Erro no reabastecimento em background: {error}")
            finally:
                self._is_replenishing = False
                self._replenish_lock.release()

        thread = threading.Thread(target=_worker, name="ProxyHarvesterReplenish", daemon=True)
        thread.start()

    def reabastecer_pool_se_vazio(self, max_concurrency: int = 250) -> None:
        """
        Recarrega o pool se estiver zerado. Se estiver abaixo do limiar mínimo mas ainda com nós,
        reabastece assincronamente em background sem pausar as threads de scraping.
        """
        total_atual = self.total_valid
        if total_atual >= self.MIN_READY_THRESHOLD:
            return

        if total_atual > 0:
            self._disparar_reabastecimento_background(max_concurrency=max_concurrency)
            return

        # Se outra thread já estiver reabastecendo, aguarda brevemente por novos nós
        if self._is_replenishing:
            for _ in range(15):
                time.sleep(0.2)
                if self.total_valid > 0:
                    return
            return

        if not self._replenish_lock.acquire(blocking=False):
            return

        try:
            self._is_replenishing = True
            logger.warning("⚠️ [PROXY-ROTATOR] Pool de proxies esgotado! Executando reabastecimento de emergência...")
            candidatos = self.carregar_novos_candidatos_com_origem()
            if not candidatos:
                with self._lock:
                    self.tested_proxies.clear()
                    self.seen_cache.clear()
                candidatos = self.carregar_novos_candidatos_com_origem()

            if not candidatos:
                logger.error("❌ [PROXY-ROTATOR] Não foi possível encontrar candidatos nas fontes públicas.")
                return

            aprovados = asyncio.run(
                self._validar_registros_em_lote(
                    candidatos,
                    max_concurrency=max_concurrency,
                    timeout=2.5,
                    mostrar_progresso=False,
                )
            )
            self._absorver_registros_aprovados(candidatos, aprovados)
            logger.info(f"✅ [PROXY-ROTATOR] Pool recarregado com {self.total_valid} proxies saudáveis.")
        finally:
            self._is_replenishing = False
            self._replenish_lock.release()

    def get_proxy(self) -> ProxyRecord | None:
        """
        Pool Manager & Dispatcher:
        Seleciona o nó ativo de menor score EWMA, priorizando nós livres (in_flight == 0)
        e incrementando in_flight para evitar colisão de concorrência.
        """
        if self.total_valid < self.MIN_READY_THRESHOLD:
            self._disparar_reabastecimento_background()

        with self._lock:
            self._sync_valid_deque_locked()
            if not self._records:
                return None

            # Ordena priorizando (1) in_flight == 0 e (2) menor priority (EWMA + falhas)
            candidatos_ativos = [rec for rec in self._records.values() if rec.is_active and rec.url not in self.dead_proxies]
            if not candidatos_ativos:
                return None

            candidatos_ativos.sort(key=lambda rec: (rec.in_flight > 0, rec.in_flight, rec.priority))
            escolhido = candidatos_ativos[0]
            escolhido.in_flight += 1
            escolhido.last_used = time.time()

            # Rotaciona a deque de compatibilidade para manter variedade se houver empate
            if self.valid_proxies and self.valid_proxies[0] == escolhido.url:
                self.valid_proxies.rotate(-1)

            return escolhido

    def release_proxy(self, proxy_str: str) -> None:
        """Libera o slot de concorrência (in_flight) do proxy após o término da requisição."""
        with self._lock:
            record = self._records.get(proxy_str)
            if record and record.in_flight > 0:
                record.in_flight -= 1

    def report_success(self, proxy_str: str, latency: float) -> None:
        """
        Inline Circuit Breaker (Feedback Positivo):
        Zera consecutive_fails, recalcula EWMA (0.7*ant + 0.3*atual) e mantém o nó no topo da fila.
        """
        with self._lock:
            record = self._records.get(proxy_str)
            if record is None:
                record = ProxyRecord(url=proxy_str, latency_ewma=max(0.05, latency), total_successes=1)
                self._records[proxy_str] = record
            else:
                if record.in_flight > 0:
                    record.in_flight -= 1
                record.record_success(latency)

            stats = self.source_stats.setdefault(record.source, {"testados": 1, "aprovados": 1, "sucessos_reais": 0})
            stats["sucessos_reais"] += 1
            self.dead_proxies.discard(proxy_str)
            self._sync_valid_deque_locked()

        self.emitir_telemetria(forcar=False)

    def report_failure(
        self,
        proxy_str: str,
        status_code: int | None = None,
        motivo: str = "falha",
        is_critical_timeout: bool = False,
    ) -> None:
        """
        Inline Circuit Breaker (Feedback Negativo):
        Avalia erro/status HTTP, aplica backoff ou expurga imediatamente nós com timeout/bloqueio.
        """
        with self._lock:
            record = self._records.get(proxy_str)
            if record is not None:
                if record.in_flight > 0:
                    record.in_flight -= 1
                manter_no_pool = record.record_failure(
                    status_code=status_code,
                    is_critical_timeout=is_critical_timeout,
                )
                if not manter_no_pool:
                    self._records.pop(proxy_str, None)
                    self.dead_proxies.add(proxy_str)
                    self._sync_valid_deque_locked()
                    logger.debug(f"🗑️ [CIRCUIT-BREAKER] Proxy expurgado ({motivo}): {proxy_str} | Ativos: {len(self.valid_proxies)}")
                else:
                    self._sync_valid_deque_locked()
                    logger.debug(
                        f"⚠️ [CIRCUIT-BREAKER] Backoff aplicado ao proxy ({motivo}): {proxy_str} (prioridade={record.priority:.2f})"
                    )
            else:
                if proxy_str in self.valid_proxies:
                    self.valid_proxies.remove(proxy_str)
                self.dead_proxies.add(proxy_str)

        if self.total_valid < self.MIN_READY_THRESHOLD:
            self._disparar_reabastecimento_background()

    def remover_proxy_invalido(self, proxy_str: str, motivo: str = "falha") -> None:
        """Método de compatibilidade que aciona expurgo imediato no Circuit Breaker."""
        with self._lock:
            self._records.pop(proxy_str, None)
            if proxy_str in self.valid_proxies:
                self.valid_proxies.remove(proxy_str)
            self.dead_proxies.add(proxy_str)
            total_restante = len(self.valid_proxies)
            logger.debug(f"🗑️ [PROXY-ROTATOR] Proxy descartado ({motivo}): {proxy_str} | Restantes no pool: {total_restante}")

    def adicionar_proxy_valido(self, proxy_str: str, latency: float = 1.0, source: str = "manual") -> None:
        """Adiciona ou revalida manualmente um proxy no pool reativo."""
        with self._lock:
            record = self._records.get(proxy_str)
            if record is None:
                self._records[proxy_str] = ProxyRecord(
                    url=proxy_str,
                    source=source,
                    latency_ewma=latency,
                    total_successes=1,
                )
            else:
                record.record_success(latency)
            self.dead_proxies.discard(proxy_str)
            self._sync_valid_deque_locked()

    def obter_proximo_proxy(self) -> dict[str, str] | None:
        """Obtém o melhor proxy disponível no formato dict para requests."""
        proxy_str = self.obter_proxima_string_proxy()
        if proxy_str:
            return {"http": proxy_str, "https": proxy_str}
        return None

    def obter_proxima_string_proxy(self) -> str | None:
        """
        Obtém a URL do proxy de melhor score EWMA com controle de concorrência.
        Se o pool estiver vazio, aciona reabastecimento.
        """
        with self._lock:
            # Caso código legado ou de teste tenha populado valid_proxies diretamente sem _records
            if self.valid_proxies and not self._records:
                for url in list(self.valid_proxies):
                    if url not in self.dead_proxies:
                        self._records[url] = ProxyRecord(url=url, latency_ewma=1.0)

        if self.total_valid == 0:
            self.reabastecer_pool_se_vazio()

        record = self.get_proxy()
        if record is not None:
            return record.url

        with self._lock:
            if not self.valid_proxies:
                return None
            selecionado = self.valid_proxies[0]
            self.valid_proxies.rotate(-1)
            return selecionado

    def obter_resumo_telemetria(self) -> dict[str, Any]:
        """Retorna métricas operacionais consolidadas para observabilidade."""
        with self._lock:
            ativos = [rec for rec in self._records.values() if rec.is_active]
            latencia_media = sum(rec.latency_ewma for rec in ativos) / len(ativos) if ativos else 0.0
            em_voo = sum(rec.in_flight for rec in ativos)
            taxa_sobrevivencia = (self._total_approved / self._total_scraped * 100.0) if self._total_scraped > 0 else 0.0
            return {
                "ready_count": len(ativos),
                "in_flight_count": em_voo,
                "dead_count": len(self.dead_proxies),
                "survival_rate_pct": round(taxa_sobrevivencia, 2),
                "avg_latency_ewma": round(latencia_media, 3),
                "sources": dict(self.source_stats),
            }

    def emitir_telemetria(self, forcar: bool = False) -> None:
        """Emite log de telemetria operacional a cada 30 segundos (ou quando forçado)."""
        agora = time.time()
        if not forcar and (agora - self._last_telemetry_ts) < 30.0:
            return
        self._last_telemetry_ts = agora
        resumo = self.obter_resumo_telemetria()
        logger.info(
            f"📊 [PROXY-TELEMETRY] Ativos={resumo['ready_count']} | "
            f"InFlight={resumo['in_flight_count']} | "
            f"Sobrevivência={resumo['survival_rate_pct']:.1f}% | "
            f"Latência EWMA Média={resumo['avg_latency_ewma']:.2f}s"
        )


# Alias compatível com toda a base de código
ProxyRotator = RealtimeProxyRotator
rotator = RealtimeProxyRotator()
