from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import aiosqlite

from config.settings import get_settings
from core.memory.base import BaseMemory

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata TEXT DEFAULT '{}',
    created_at REAL NOT NULL
);
"""

_CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_memory_session ON memory(session_id);
"""


class PersistentMemory(BaseMemory):
    """SQLite-backed memory that survives restarts, scoped by session_id."""

    def __init__(self, session_id: str, db_path: str | None = None):
        self.session_id = session_id
        settings = get_settings()
        self._db_path = db_path or settings.db_path
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialised = False

    async def _ensure_table(self) -> None:
        if self._initialised:
            return
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(_CREATE_TABLE)
            await db.execute(_CREATE_INDEX)
            await db.commit()
        self._initialised = True

    async def add_message(self, role: str, content: str, **metadata: Any) -> None:
        await self._ensure_table()
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "INSERT INTO memory (session_id, role, content, metadata, created_at) VALUES (?, ?, ?, ?, ?)",
                (self.session_id, role, content, json.dumps(metadata), time.time()),
            )
            await db.commit()

    async def get_messages(self, limit: int | None = None) -> list[dict[str, Any]]:
        await self._ensure_table()
        query = "SELECT role, content FROM memory WHERE session_id = ? ORDER BY id ASC"
        params: list[Any] = [self.session_id]
        if limit:
            query += " LIMIT ?"
            params.append(limit)

        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in rows]

    async def clear(self) -> None:
        await self._ensure_table()
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("DELETE FROM memory WHERE session_id = ?", (self.session_id,))
            await db.commit()

    async def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        await self._ensure_table()
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT role, content FROM memory WHERE session_id = ? AND content LIKE ? ORDER BY id DESC LIMIT ?",
                (self.session_id, f"%{query}%", top_k),
            ) as cursor:
                rows = await cursor.fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in rows]
