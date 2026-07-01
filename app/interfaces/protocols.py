"""Service port protocols for dependency injection."""

from __future__ import annotations

from typing import Protocol


class AIRouterServiceProtocol(Protocol):
    """Placeholder protocol for the future AI router service (Phase 2)."""

    async def route(self, intent: str) -> str:
        """Route an intent to the appropriate agent."""
        ...


class MemoryServiceProtocol(Protocol):
    """Placeholder protocol for the future memory service (Phase 3)."""

    async def retrieve(self, query: str) -> list[str]:
        """Retrieve relevant memories for a query."""
        ...


class ToolServiceProtocol(Protocol):
    """Placeholder protocol for the future tool framework (Phase 4)."""

    async def invoke(self, tool_name: str, params: dict[str, object]) -> object:
        """Invoke a registered tool."""
        ...
