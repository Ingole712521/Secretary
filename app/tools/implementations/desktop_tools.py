"""Desktop automation tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.tools.desktop.exceptions import DesktopAutomationError
from app.tools.interfaces.base_tool import BaseTool
from app.tools.results.models import ToolResult
from app.tools.schemas.enums import ToolCategory, ToolPermissionLevel
from app.tools.schemas.parameters import ToolParameter

if TYPE_CHECKING:
    from app.tools.desktop.interfaces.desktop_automation import DesktopAutomation


class _DesktopToolBase(BaseTool):
    """Shared desktop tool behavior."""

    def __init__(self, desktop: DesktopAutomation) -> None:
        """Initialize with a desktop automation adapter.

        Args:
            desktop: Platform desktop automation port.
        """
        self._desktop = desktop

    @property
    def category(self) -> ToolCategory:
        """Desktop tools belong to the automation category."""
        return ToolCategory.AUTOMATION

    async def health(self) -> bool:
        """Delegate health checks to the desktop adapter."""
        return await self._desktop.health()

    async def _run_desktop_action(
        self,
        action: str,
        callback: Any,
    ) -> ToolResult:
        """Execute a desktop action with consistent error handling.

        Args:
            action: Action name for logging and messages.
            callback: Async callable returning structured output.

        Returns:
            Tool result for the action.
        """
        if not self._desktop.is_supported:
            return ToolResult.failure(
                error="Desktop automation is not supported on this platform",
                message=f"{action} is unavailable on {self._desktop.platform_name}",
            )

        try:
            output = await callback()
        except DesktopAutomationError as exc:
            return ToolResult.failure(error=exc.message, message=str(exc))
        except Exception as exc:  # noqa: BLE001
            return ToolResult.failure(
                error=str(exc),
                message=f"Desktop {action} failed",
            )

        return ToolResult.success(
            output=output,
            message=f"Desktop {action} completed",
        )


class FocusWindowTool(_DesktopToolBase):
    """Bring a window to the foreground by title."""

    @property
    def id(self) -> str:
        """Tool identifier."""
        return "desktop.focus_window"

    @property
    def name(self) -> str:
        """Tool name."""
        return "Focus Window"

    @property
    def description(self) -> str:
        """Tool description."""
        return (
            "Focus a desktop window whose title contains the given text. "
            "Use before typing into an application."
        )

    @property
    def parameters(self) -> list[ToolParameter]:
        """Tool parameters."""
        return [
            ToolParameter(
                name="title",
                type="string",
                description="Substring of the target window title",
                required=True,
            ),
        ]

    @property
    def permissions(self) -> list[ToolPermissionLevel]:
        """Required permissions."""
        return [ToolPermissionLevel.READ, ToolPermissionLevel.EXECUTE]

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        """Focus a window."""
        title = str(params["title"])
        return await self._run_desktop_action(
            "focus_window",
            lambda: self._desktop.focus_window(title),
        )


class ClickTool(_DesktopToolBase):
    """Click at screen coordinates."""

    @property
    def id(self) -> str:
        """Tool identifier."""
        return "desktop.click"

    @property
    def name(self) -> str:
        """Tool name."""
        return "Mouse Click"

    @property
    def description(self) -> str:
        """Tool description."""
        return "Click the mouse at the given screen coordinates."

    @property
    def parameters(self) -> list[ToolParameter]:
        """Tool parameters."""
        return [
            ToolParameter(
                name="x",
                type="integer",
                description="Horizontal screen coordinate",
                required=True,
            ),
            ToolParameter(
                name="y",
                type="integer",
                description="Vertical screen coordinate",
                required=True,
            ),
            ToolParameter(
                name="button",
                type="string",
                description="Mouse button: left, right, or middle",
                required=False,
                default="left",
                enum=["left", "right", "middle"],
            ),
        ]

    @property
    def permissions(self) -> list[ToolPermissionLevel]:
        """Required permissions."""
        return [ToolPermissionLevel.EXECUTE, ToolPermissionLevel.WRITE]

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        """Click the mouse."""
        x = int(params["x"])
        y = int(params["y"])
        button = str(params.get("button", "left"))
        return await self._run_desktop_action(
            "click",
            lambda: self._desktop.click(x, y, button=button),
        )


class TypeTextTool(_DesktopToolBase):
    """Type text using the keyboard."""

    @property
    def id(self) -> str:
        """Tool identifier."""
        return "desktop.type_text"

    @property
    def name(self) -> str:
        """Tool name."""
        return "Type Text"

    @property
    def description(self) -> str:
        """Tool description."""
        return (
            "Type text into the currently focused window. "
            "Focus the target application first with desktop.focus_window."
        )

    @property
    def parameters(self) -> list[ToolParameter]:
        """Tool parameters."""
        return [
            ToolParameter(
                name="text",
                type="string",
                description="Text to type",
                required=True,
            ),
            ToolParameter(
                name="interval",
                type="number",
                description="Delay between keystrokes in seconds",
                required=False,
                default=0.02,
            ),
        ]

    @property
    def permissions(self) -> list[ToolPermissionLevel]:
        """Required permissions."""
        return [ToolPermissionLevel.EXECUTE, ToolPermissionLevel.WRITE]

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        """Type text."""
        text = str(params["text"])
        interval = float(params.get("interval", 0.02))
        return await self._run_desktop_action(
            "type_text",
            lambda: self._desktop.type_text(text, interval=interval),
        )


class ScreenshotRegionTool(_DesktopToolBase):
    """Capture a rectangular screen region."""

    @property
    def id(self) -> str:
        """Tool identifier."""
        return "desktop.screenshot_region"

    @property
    def name(self) -> str:
        """Tool name."""
        return "Screenshot Region"

    @property
    def description(self) -> str:
        """Tool description."""
        return (
            "Capture a rectangular region of the screen and return a "
            "base64-encoded PNG image."
        )

    @property
    def parameters(self) -> list[ToolParameter]:
        """Tool parameters."""
        return [
            ToolParameter(
                name="x",
                type="integer",
                description="Region left coordinate",
                required=True,
            ),
            ToolParameter(
                name="y",
                type="integer",
                description="Region top coordinate",
                required=True,
            ),
            ToolParameter(
                name="width",
                type="integer",
                description="Region width in pixels",
                required=True,
            ),
            ToolParameter(
                name="height",
                type="integer",
                description="Region height in pixels",
                required=True,
            ),
        ]

    @property
    def permissions(self) -> list[ToolPermissionLevel]:
        """Required permissions."""
        return [ToolPermissionLevel.READ]

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        """Capture a screenshot region."""
        x = int(params["x"])
        y = int(params["y"])
        width = int(params["width"])
        height = int(params["height"])
        return await self._run_desktop_action(
            "screenshot_region",
            lambda: self._desktop.screenshot_region(x, y, width, height),
        )
