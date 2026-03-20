from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMResponse:
    content: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    raw: Any = None
    usage: dict[str, int] = field(default_factory=dict)


class BaseLLMProvider(ABC):
    """Abstract interface every LLM provider must implement."""

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
        model: str | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Send a chat completion request and return a normalised response."""
        ...

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
        model: str | None = None,
        **kwargs: Any,
    ):
        """Yield streamed chunks from the provider."""
        ...
