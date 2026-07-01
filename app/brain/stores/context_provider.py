"""Stub context provider for Sprint 2 architecture."""

from __future__ import annotations

from typing import Any

from app.brain.schemas.context import ExecutionContext
from app.brain.schemas.conversation import Conversation


class StubContextProvider:
    """Minimal context provider implementing ``ContextProvider``.

    Returns empty memory and basic environment metadata. Future sprints
    will replace memory retrieval with the Memory subsystem adapter.
    """

    def __init__(self, app_env: str, app_version: str) -> None:
        """Initialize with application metadata.

        Args:
            app_env: Current deployment environment.
            app_version: Application version string.
        """
        self._app_env = app_env
        self._app_version = app_version
        self._sessions: dict[str, dict[str, Any]] = {}

    async def get_session_context(self, session_id: str | None) -> dict[str, Any]:
        """Load ephemeral session context."""
        if session_id is None:
            return {}
        return self._sessions.setdefault(session_id, {})

    async def get_environment_context(self) -> dict[str, Any]:
        """Load deployment and runtime environment context."""
        return {
            "app_env": self._app_env,
            "app_version": self._app_version,
        }

    async def get_memory_context(
        self,
        query: str,
        conversation: Conversation | None = None,
    ) -> list[dict[str, Any]]:
        """Return empty memory — placeholder for future Memory subsystem."""
        _ = query, conversation
        return []

    async def build_context(
        self,
        conversation: Conversation | None,
        session_id: str | None = None,
    ) -> ExecutionContext:
        """Assemble a full execution context from available sources."""
        return ExecutionContext(
            conversation=conversation,
            session=await self.get_session_context(session_id),
            environment=await self.get_environment_context(),
            memory=await self.get_memory_context(
                query="",
                conversation=conversation,
            ),
        )
