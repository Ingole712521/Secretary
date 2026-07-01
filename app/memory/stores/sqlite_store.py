"""SQLite-backed memory store."""

from __future__ import annotations

import asyncio
import json
import sqlite3
from pathlib import Path
from typing import Any

from app.memory.schemas.models import MemoryFact, MemorySearchResult
from app.memory.search import score_memory_match


class SqliteMemoryStore:
    """Persistent memory store using SQLite.

    Blocking database calls run in a thread pool to keep the async API
    non-blocking.

    Attributes:
        _db_path: Path to the SQLite database file.
    """

    def __init__(self, db_path: Path) -> None:
        """Initialize the SQLite memory store.

        Args:
            db_path: Filesystem path for the SQLite database.
        """
        self._db_path = db_path
        self._initialized = False
        self._init_lock = asyncio.Lock()

    async def store(self, fact: MemoryFact) -> MemoryFact:
        """Persist a memory fact."""
        await self._ensure_initialized()
        fact.touch()
        await asyncio.to_thread(self._upsert_fact, fact)
        return fact

    async def get(self, memory_id: str) -> MemoryFact | None:
        """Retrieve a fact by ID."""
        await self._ensure_initialized()
        return await asyncio.to_thread(self._get_fact, memory_id)

    async def delete(self, memory_id: str) -> bool:
        """Delete a fact by ID."""
        await self._ensure_initialized()
        return await asyncio.to_thread(self._delete_fact, memory_id)

    async def search(self, query: str, *, limit: int = 10) -> list[MemorySearchResult]:
        """Search facts using keyword relevance scoring."""
        await self._ensure_initialized()
        facts = await asyncio.to_thread(self._load_all_facts)
        ranked: list[MemorySearchResult] = []

        for fact in facts:
            score = score_memory_match(query, fact.content, fact.tags)
            if score > 0:
                ranked.append(MemorySearchResult(fact=fact, score=score))

        ranked.sort(key=lambda item: (item.score, item.fact.updated_at), reverse=True)
        return ranked[:limit]

    async def list_facts(self, *, limit: int = 100) -> list[MemoryFact]:
        """List facts ordered by most recently updated."""
        await self._ensure_initialized()
        facts = await asyncio.to_thread(self._load_all_facts)
        facts.sort(key=lambda fact: fact.updated_at, reverse=True)
        return facts[:limit]

    async def _ensure_initialized(self) -> None:
        """Create database schema on first use."""
        async with self._init_lock:
            if self._initialized:
                return
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            await asyncio.to_thread(self._initialize_schema)
            self._initialized = True

    def _initialize_schema(self) -> None:
        """Create tables if they do not exist."""
        with sqlite3.connect(self._db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_facts (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    category TEXT,
                    tags TEXT NOT NULL,
                    source TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def _upsert_fact(self, fact: MemoryFact) -> None:
        """Insert or replace a memory fact."""
        with sqlite3.connect(self._db_path) as connection:
            connection.execute(
                """
                INSERT INTO memory_facts (
                    id, content, category, tags, source, metadata,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    content = excluded.content,
                    category = excluded.category,
                    tags = excluded.tags,
                    source = excluded.source,
                    metadata = excluded.metadata,
                    updated_at = excluded.updated_at
                """,
                (
                    fact.id,
                    fact.content,
                    fact.category,
                    json.dumps(fact.tags),
                    fact.source,
                    json.dumps(fact.metadata),
                    fact.created_at.isoformat(),
                    fact.updated_at.isoformat(),
                ),
            )
            connection.commit()

    def _get_fact(self, memory_id: str) -> MemoryFact | None:
        """Load a single fact by ID."""
        with sqlite3.connect(self._db_path) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                "SELECT * FROM memory_facts WHERE id = ?",
                (memory_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_fact(row)

    def _delete_fact(self, memory_id: str) -> bool:
        """Delete a fact and return whether a row was removed."""
        with sqlite3.connect(self._db_path) as connection:
            cursor = connection.execute(
                "DELETE FROM memory_facts WHERE id = ?",
                (memory_id,),
            )
            connection.commit()
            return cursor.rowcount > 0

    def _load_all_facts(self) -> list[MemoryFact]:
        """Load all facts from the database."""
        with sqlite3.connect(self._db_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute("SELECT * FROM memory_facts").fetchall()
        return [self._row_to_fact(row) for row in rows]

    @staticmethod
    def _row_to_fact(row: sqlite3.Row) -> MemoryFact:
        """Convert a database row to a ``MemoryFact``."""
        from datetime import datetime

        metadata_raw = row["metadata"]
        tags_raw = row["tags"]
        metadata: dict[str, Any] = json.loads(metadata_raw)
        tags: list[str] = json.loads(tags_raw)

        return MemoryFact(
            id=row["id"],
            content=row["content"],
            category=row["category"],
            tags=tags,
            source=row["source"],
            metadata=metadata,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
