"""Context provider port interface."""

from __future__ import annotations

from typing import Any, Protocol

from app.brain.schemas.context import ExecutionContext
from app.brain.schemas.conversation import Conversation


class ContextProvider(Protocol):
    """Port for supplying environment and session context fragments.

    Future implementations may load context from memory stores,
    environment probes, or external configuration services.
    """

    async def get_session_context(self, session_id: str | None) -> dict[str, Any]:
        """Load ephemeral session context.

        Args:
            session_id: Optional session identifier.

        Returns:
            Session key-value context.
        """
        ...

    async def get_environment_context(self) -> dict[str, Any]:
        """Load deployment and runtime environment context.

        Returns:
            Environment metadata dictionary.
        """
        ...

    async def get_memory_context(
        self,
        query: str,
        conversation: Conversation | None = None,
    ) -> list[dict[str, Any]]:
        """Load relevant memory entries for a query.

        Sprint 2 returns an empty list. Memory subsystem will
        implement this in a future sprint.

        Args:
            query: User query for memory retrieval.
            conversation: Optional active conversation.

        Returns:
            List of memory entry dictionaries.
        """
        ...

    async def build_context(
        self,
        conversation: Conversation | None,
        session_id: str | None = None,
    ) -> ExecutionContext:
        """Assemble a full execution context.

        Args:
            conversation: Active conversation, if any.
            session_id: Optional session identifier.

        Returns:
            Merged execution context.
        """
        ...
