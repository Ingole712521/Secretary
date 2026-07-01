"""Base tool implementation with default behavior."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.tools.results.models import ToolResult
from app.tools.schemas.enums import ToolCategory, ToolPermissionLevel
from app.tools.schemas.parameters import ToolParameter


class BaseTool(ABC):
    """Abstract base class for tool implementations.

    Subclasses must implement ``execute``. Default implementations are
    provided for ``validate``, ``dry_run``, and ``health``.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique tool identifier."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable tool name."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""

    @property
    @abstractmethod
    def category(self) -> ToolCategory:
        """Tool category."""

    @property
    @abstractmethod
    def parameters(self) -> list[ToolParameter]:
        """Declared parameters."""

    @property
    @abstractmethod
    def permissions(self) -> list[ToolPermissionLevel]:
        """Required permissions."""

    @abstractmethod
    async def execute(self, params: dict[str, Any]) -> ToolResult:
        """Execute the tool."""

    async def validate(self, params: dict[str, Any]) -> ToolResult:
        """Default validation delegates to dry run semantics.

        Args:
            params: Input parameters.

        Returns:
            Success if parameters appear valid.
        """
        return await self.dry_run(params)

    async def dry_run(self, params: dict[str, Any]) -> ToolResult:
        """Default dry run reports readiness without side effects.

        Args:
            params: Input parameters.

        Returns:
            Success result with dry-run metadata.
        """
        _ = params
        return ToolResult.success(
            output={"dry_run": True, "tool_id": self.id},
            message=f"Dry run successful for {self.name}",
        )

    async def health(self) -> bool:
        """Default health check returns True.

        Returns:
            True indicating the tool is operational.
        """
        return True

    def to_definition(self) -> dict[str, Any]:
        """Export tool metadata as a dictionary.

        Returns:
            Serializable tool metadata.
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "parameters": [p.model_dump() for p in self.parameters],
            "permissions": [p.value for p in self.permissions],
        }
