from __future__ import annotations

from core.llm.base import BaseLLMProvider


class LLMRegistry:
    """Singleton registry mapping provider names to LLM provider instances."""

    _providers: dict[str, BaseLLMProvider] = {}
    _default: str | None = None

    @classmethod
    def register(cls, provider: BaseLLMProvider, *, default: bool = False) -> None:
        cls._providers[provider.provider_name] = provider
        if default or cls._default is None:
            cls._default = provider.provider_name

    @classmethod
    def get(cls, name: str | None = None) -> BaseLLMProvider:
        key = name or cls._default
        if key is None or key not in cls._providers:
            raise KeyError(
                f"LLM provider '{key}' not found. "
                f"Available: {list(cls._providers.keys())}"
            )
        return cls._providers[key]

    @classmethod
    def list_providers(cls) -> list[str]:
        return list(cls._providers.keys())

    @classmethod
    def clear(cls) -> None:
        cls._providers.clear()
        cls._default = None


def setup_default_providers() -> None:
    """Instantiate and register the default providers from settings."""
    from config.settings import get_settings
    from core.llm.azure_openai import AzureOpenAIProvider

    settings = get_settings()
    if settings.azure_open_ai_key:
        LLMRegistry.register(AzureOpenAIProvider(), default=True)
