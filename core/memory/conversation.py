from __future__ import annotations

from typing import Any

from core.memory.base import BaseMemory


class ConversationMemory(BaseMemory):
    """In-memory conversation history with optional sliding window."""

    def __init__(self, max_messages: int | None = None):
        self._messages: list[dict[str, Any]] = []
        self._max_messages = max_messages

    async def add_message(self, role: str, content: str, **metadata: Any) -> None:
        entry: dict[str, Any] = {"role": role, "content": content}
        if metadata:
            entry["metadata"] = metadata
        self._messages.append(entry)

        if self._max_messages and len(self._messages) > self._max_messages:
            self._messages = self._messages[-self._max_messages:]

    async def get_messages(self, limit: int | None = None) -> list[dict[str, Any]]:
        msgs = self._messages if limit is None else self._messages[-limit:]
        return [{"role": m["role"], "content": m["content"]} for m in msgs]

    async def clear(self) -> None:
        self._messages.clear()

    async def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        query_lower = query.lower()
        scored = []
        for m in self._messages:
            content = m["content"].lower()
            if query_lower in content:
                scored.append(m)
        return scored[:top_k]
