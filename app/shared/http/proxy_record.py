import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(order=True)
class ProxyRecord:
    """Registro de estado e métricas de um nó de proxy para fila prioritária e Circuit Breaker."""

    # Prioridade para PriorityQueue / Min-Heap (menor valor = maior prioridade)
    priority: float = field(init=False, default=1.0)

    url: str = field(compare=False, default="")
    source: str = field(compare=False, default="unknown")
    latency_ewma: float = field(default=1.0, compare=False)
    in_flight: int = field(default=0, compare=False)
    consecutive_fails: int = field(default=0, compare=False)
    total_successes: int = field(default=0, compare=False)
    total_failures: int = field(default=0, compare=False)
    last_used: float = field(default_factory=time.time, compare=False)
    created_at: float = field(default_factory=time.time, compare=False)
    is_active: bool = field(default=True, compare=False)

    def __post_init__(self) -> None:
        self.calculate_priority()

    def calculate_priority(self) -> float:
        """Score baseado em latência ponderada (EWMA) e histórico de falhas consecutivas."""
        self.priority = self.latency_ewma * (1.0 + (self.consecutive_fails * 2.0))
        return self.priority

    def record_success(self, current_latency: float) -> float:
        """
        Registra sucesso de requisição real, zera falhas consecutivas e recalcula EWMA:
        EWMA_nova = 0.7 * EWMA_anterior + 0.3 * Latência_atual
        """
        clamped_latency = max(0.05, float(current_latency))
        if self.total_successes == 0:
            self.latency_ewma = clamped_latency
        else:
            self.latency_ewma = (0.7 * self.latency_ewma) + (0.3 * clamped_latency)

        self.consecutive_fails = 0
        self.total_successes += 1
        self.last_used = time.time()
        self.is_active = True
        return self.calculate_priority()

    def record_failure(self, status_code: int | None = None, is_critical_timeout: bool = False) -> bool:
        """
        Registra falha na execução do tráfego real e aciona o Circuit Breaker.
        Retorna True se o proxy ainda puder permanecer no pool (backoff), ou False se deve ser expurgado.
        """
        self.consecutive_fails += 1
        self.total_failures += 1
        self.last_used = time.time()

        # Expurgo imediato em timeout/reset crítico ou bloqueios severos (403, 407, 429)
        if is_critical_timeout or status_code in {401, 403, 407, 429, 999}:
            if self.consecutive_fails >= 1 and (is_critical_timeout or status_code in {407, 429, 999}):
                self.is_active = False
                return False
            if self.consecutive_fails >= 2:
                self.is_active = False
                return False

        # Qualquer outro erro que atinja 2 falhas consecutivas causa expurgo
        if self.consecutive_fails >= 2:
            self.is_active = False
            return False

        self.calculate_priority()
        return True

    def is_expired(self, ttl_seconds: float = 600.0) -> bool:
        """Verifica se o nó ficou inativo além do TTL (prevenção de Buffer Bloat)."""
        return (time.time() - self.last_used) > ttl_seconds

    def is_tier_a(self) -> bool:
        """Determina se o proxy tem alta confiabilidade comprovada para persistência Tier-A."""
        return self.is_active and self.consecutive_fails == 0 and self.latency_ewma <= 2.2 and self.total_successes >= 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "source": self.source,
            "latency_ewma": round(self.latency_ewma, 4),
            "total_successes": self.total_successes,
            "total_failures": self.total_failures,
            "last_used": self.last_used,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProxyRecord":
        return cls(
            url=str(data.get("url", "")),
            source=str(data.get("source", "tier_a_cache")),
            latency_ewma=float(data.get("latency_ewma", 1.0)),
            total_successes=int(data.get("total_successes", 1)),
            total_failures=int(data.get("total_failures", 0)),
            last_used=float(data.get("last_used", time.time())),
        )
