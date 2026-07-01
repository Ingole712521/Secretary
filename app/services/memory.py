"""Long-term memory application service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.memory.schemas.models import MemoryFact
from app.models.memory import (
    MemoryCreateRequest,
    MemoryFactResponse,
    MemorySearchResponse,
    MemorySearchResultItem,
)

if TYPE_CHECKING:
    from app.config.settings import Settings
    from app.memory.interfaces.memory_store import MemoryStore


class MemoryService:
    """Orchestrates long-term memory storage and retrieval.

    Attributes:
        _store: Memory persistence port.
        _settings: Application settings.
    """

    def __init__(self, store: MemoryStore, settings: Settings) -> None:
        """Initialize the memory service.

        Args:
            store: Memory store adapter.
            settings: Application settings.
        """
        self._store = store
        self._settings = settings

    async def store_fact(self, request: MemoryCreateRequest) -> MemoryFactResponse:
        """Store a new memory fact.

        Args:
            request: Validated create request.

        Returns:
            Stored fact response.
        """
        fact = MemoryFact(
            content=request.content,
            category=request.category,
            tags=request.tags,
            source=request.source,
        )
        stored = await self._store.store(fact)
        return _to_response(stored)

    async def search_facts(
        self,
        query: str,
        *,
        limit: int | None = None,
    ) -> MemorySearchResponse:
        """Search memory facts by keyword relevance.

        Args:
            query: Search query string.
            limit: Optional result limit override.

        Returns:
            Ranked search results.
        """
        resolved_limit = limit or self._settings.memory_search_limit
        results = await self._store.search(query, limit=resolved_limit)
        return MemorySearchResponse(
            query=query,
            results=[
                MemorySearchResultItem(
                    id=result.fact.id,
                    content=result.fact.content,
                    category=result.fact.category,
                    tags=result.fact.tags,
                    score=result.score,
                    updated_at=result.fact.updated_at,
                )
                for result in results
            ],
        )

    async def relevant_facts_for_message(
        self,
        message: str,
        *,
        limit: int | None = None,
    ) -> list[MemoryFact]:
        """Return facts relevant to a user message for chat context.

        Args:
            message: Current user message.
            limit: Optional result limit override.

        Returns:
            Relevant memory facts, highest score first.
        """
        if not self._settings.memory_enabled:
            return []

        resolved_limit = limit or self._settings.memory_context_limit
        results = await self._store.search(message, limit=resolved_limit)
        return [result.fact for result in results]

    @staticmethod
    def format_facts_for_prompt(facts: list[MemoryFact]) -> str:
        """Format memory facts as a system prompt block.

        Args:
            facts: Relevant memory facts.

        Returns:
            Formatted bullet list for injection into chat context.
        """
        lines = [f"- {fact.content}" for fact in facts]
        return "Known facts about the user:\n" + "\n".join(lines)


def _to_response(fact: MemoryFact) -> MemoryFactResponse:
    """Map a domain fact to an API response."""
    return MemoryFactResponse(
        id=fact.id,
        content=fact.content,
        category=fact.category,
        tags=fact.tags,
        source=fact.source,
        created_at=fact.created_at,
        updated_at=fact.updated_at,
    )
