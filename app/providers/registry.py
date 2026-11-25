from typing import ClassVar

from app.core.config import Settings
from app.providers.base import JobProviderStrategy


class ProviderRegistry:
    _providers: ClassVar[dict[str, type[JobProviderStrategy]]] = {}

    @classmethod
    def register(cls, provider_cls: type[JobProviderStrategy]) -> type[JobProviderStrategy]:
        chave = provider_cls.provider_name.strip().lower()
        cls._providers[chave] = provider_cls
        return provider_cls

    @classmethod
    def get_all_providers(cls) -> list[JobProviderStrategy]:
        return [provider_cls() for provider_cls in cls._providers.values()]

    @classmethod
    def get_active_providers(cls, settings: Settings) -> list[JobProviderStrategy]:
        ativos: list[JobProviderStrategy] = []
        for provider_cls in cls._providers.values():
            instancia = provider_cls()
            if instancia.is_enabled(settings):
                ativos.append(instancia)
        return ativos

    @classmethod
    def get_badge_colors(cls, provider_name: str) -> tuple[str, str]:
        chave = (provider_name or "").strip().lower()
        if chave in cls._providers:
            return cls._providers[chave].badge_colors
        for chave_registrada, provider_cls in cls._providers.items():
            if chave_registrada in chave or chave in chave_registrada:
                return provider_cls.badge_colors
        return ("#475569", "#ffffff")
