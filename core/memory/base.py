from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseMemory(ABC):
    """Interface for agent memory backends."""

    @abstractmethod
    async def add_message(self, role: str, content: str, **metadata: Any) -> None: ...

    @abstractmethod
    async def get_messages(self, limit: int | None = None) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def clear(self) -> None: ...

    @abstractmethod
    async def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Semantic or keyword search over stored messages."""
        ...
