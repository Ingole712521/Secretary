"""SQLite memory store tests."""

from __future__ import annotations

import pytest

from app.memory.schemas.models import MemoryFact
from app.memory.stores.sqlite_store import SqliteMemoryStore


@pytest.fixture
def store(tmp_path: object) -> SqliteMemoryStore:
    """Return an isolated SQLite memory store."""
    return SqliteMemoryStore(tmp_path / "memory.db")  # type: ignore[operator]


@pytest.mark.asyncio
async def test_store_and_get_fact(store: SqliteMemoryStore) -> None:
    """Facts persist and can be retrieved by ID."""
    fact = MemoryFact(content="User's name is Nehal", tags=["personal"])
    stored = await store.store(fact)

    loaded = await store.get(stored.id)

    assert loaded is not None
    assert loaded.content == "User's name is Nehal"
    assert loaded.tags == ["personal"]


@pytest.mark.asyncio
async def test_search_finds_relevant_facts(store: SqliteMemoryStore) -> None:
    """Search returns facts matching query keywords."""
    await store.store(MemoryFact(content="User's name is Nehal", tags=["personal"]))
    await store.store(
        MemoryFact(content="Favorite editor is VS Code", tags=["preference"]),
    )

    results = await store.search("Nehal name")

    assert len(results) == 1
    assert "Nehal" in results[0].fact.content
    assert results[0].score > 0


@pytest.mark.asyncio
async def test_delete_fact(store: SqliteMemoryStore) -> None:
    """Deleted facts are no longer retrievable."""
    stored = await store.store(MemoryFact(content="Temporary fact"))

    deleted = await store.delete(stored.id)
    loaded = await store.get(stored.id)

    assert deleted is True
    assert loaded is None
