"""Register production tools with the tool platform."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.tools.implementations.terminal import TerminalTool
from app.tools.registry.registry import ToolRegistry

if TYPE_CHECKING:
    from app.config.settings import Settings


def register_production_tools(
    registry: ToolRegistry,
    settings: Settings,
) -> None:
    """Register built-in tools available in production.

    Args:
        registry: Tool registry to populate.
        settings: Application settings for tool configuration.
    """
    if not settings.tools_enabled:
        return

    registry.register(
        TerminalTool(timeout_seconds=float(settings.terminal_command_timeout)),
    )
