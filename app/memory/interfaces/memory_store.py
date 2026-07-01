"""Memory store port interface."""

from __future__ import annotations

from typing import Protocol

from app.memory.schemas.models import MemoryFact, MemorySearchResult


class MemoryStore(Protocol):
    """Port for persistent long-term memory storage."""

    async def store(self, fact: MemoryFact) -> MemoryFact:
        """Persist a memory fact.

        Args:
            fact: Fact to store or update.

        Returns:
            Stored fact.
        """
        ...

    async def get(self, memory_id: str) -> MemoryFact | None:
        """Retrieve a fact by ID.

        Args:
            memory_id: Memory identifier.

        Returns:
            Fact if found, otherwise None.
        """
        ...

    async def delete(self, memory_id: str) -> bool:
        """Delete a fact by ID.

        Args:
            memory_id: Memory identifier.

        Returns:
            True if a fact was deleted.
        """
        ...

    async def search(self, query: str, *, limit: int = 10) -> list[MemorySearchResult]:
        """Search facts by keyword relevance.

        Args:
            query: Search query string.
            limit: Maximum results to return.

        Returns:
            Ranked search results.
        """
        ...

    async def list_facts(self, *, limit: int = 100) -> list[MemoryFact]:
        """List stored facts ordered by most recently updated.

        Args:
            limit: Maximum facts to return.

        Returns:
            List of memory facts.
        """
        ...
