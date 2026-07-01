"""Test-only stub tool for framework validation.

Not registered in production. Used only in tool platform tests.
"""

from __future__ import annotations

from typing import Any

from app.tools.interfaces.base_tool import BaseTool
from app.tools.results.models import ToolResult
from app.tools.schemas.enums import ToolCategory, ToolPermissionLevel
from app.tools.schemas.parameters import ToolParameter


class StubEchoTool(BaseTool):
    """Minimal stub tool for testing the tool platform framework."""

    @property
    def id(self) -> str:
        """Tool identifier."""
        return "test.echo"

    @property
    def name(self) -> str:
        """Tool name."""
        return "Echo (Test Stub)"

    @property
    def description(self) -> str:
        """Tool description."""
        return "Framework test stub — echoes input"

    @property
    def category(self) -> ToolCategory:
        """Tool category."""
        return ToolCategory.SYSTEM

    @property
    def parameters(self) -> list[ToolParameter]:
        """Tool parameters."""
        return [
            ToolParameter(
                name="message",
                type="string",
                description="Message to echo",
                required=True,
            ),
        ]

    @property
    def permissions(self) -> list[ToolPermissionLevel]:
        """Required permissions."""
        return [ToolPermissionLevel.READ, ToolPermissionLevel.EXECUTE]

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        """Echo the message parameter."""
        return ToolResult.success(
            output={"echo": params.get("message", "")},
            message="Echo stub executed",
        )
