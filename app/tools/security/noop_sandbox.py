"""No-op sandbox stub for Sprint 3 interface validation."""

from __future__ import annotations


class NoOpSandbox:
    """Sandbox stub that performs no isolation.

      Implements the ``Sandbox`` protocol for framework testing.
    Production sandboxes will replace this in a future sprint.
    """

    async def prepare(self, tool_id: str) -> None:
        """No-op prepare."""
        _ = tool_id

    async def execute_isolated(self, tool_id: str, params: dict[str, object]) -> object:
        """Return params unchanged."""
        _ = tool_id
        return params

    async def cleanup(self, tool_id: str) -> None:
        """No-op cleanup."""
        _ = tool_id
