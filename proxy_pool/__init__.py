from proxy_pool.client import requisicao_com_rotacao
from proxy_pool.record import ProxyRecord
from proxy_pool.rotator import ProxyRotator, RealtimeProxyRotator, rotator
from proxy_pool.sources import (
    DEFAULT_HEADERS,
    INVALID_PROXY_BODY_MARKERS,
    ProxySourcesCollector,
    sanitizar_esquema_proxy,
    validar_integridade_semantica_resposta,
)

__all__ = [
    "DEFAULT_HEADERS",
    "INVALID_PROXY_BODY_MARKERS",
    "ProxyRecord",
    "ProxyRotator",
    "ProxySourcesCollector",
    "RealtimeProxyRotator",
    "requisicao_com_rotacao",
    "rotator",
    "sanitizar_esquema_proxy",
    "validar_integridade_semantica_resposta",
]
