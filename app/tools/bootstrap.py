"""Register production tools with the tool platform."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.tools.desktop.factory import build_desktop_automation
from app.tools.implementations.app_tools import OpenAppTool
from app.tools.implementations.cursor_tools import OpenCursorProjectTool
from app.tools.implementations.desktop_tools import (
    ClickTool,
    FocusWindowTool,
    ScreenshotRegionTool,
    TypeTextTool,
)
from app.tools.implementations.terminal import TerminalTool

if TYPE_CHECKING:
    from app.config.settings import Settings
    from app.tools.desktop.interfaces.desktop_automation import DesktopAutomation
    from app.tools.registry.registry import ToolRegistry


def register_production_tools(
    registry: ToolRegistry,
    settings: Settings,
    desktop: DesktopAutomation | None = None,
) -> None:
    """Register built-in tools available in production.

    Args:
        registry: Tool registry to populate.
        settings: Application settings for tool configuration.
        desktop: Optional desktop adapter override for tests.
    """
    if not settings.tools_enabled:
        return

    registry.register(
        TerminalTool(timeout_seconds=float(settings.terminal_command_timeout)),
    )
    registry.register(OpenAppTool())
    registry.register(
        OpenCursorProjectTool(
            roots=settings.cursor_project_roots,
            max_depth=settings.cursor_project_search_depth,
        ),
    )

    if not settings.desktop_automation_enabled:
        return

    automation = desktop or build_desktop_automation()
    registry.register(FocusWindowTool(automation))
    registry.register(ClickTool(automation))
    registry.register(TypeTextTool(automation))
    registry.register(ScreenshotRegionTool(automation))
