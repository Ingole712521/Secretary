"""Windows desktop automation adapter."""

from __future__ import annotations

import asyncio
import base64
import io
import platform
from typing import Any

from app.tools.desktop.exceptions import DesktopAutomationError


class WindowsDesktopAutomation:
    """Windows desktop automation using ``pygetwindow`` and ``pyautogui``.

    Blocking GUI calls are executed in a thread pool to avoid blocking
    the asyncio event loop.

    Attributes:
        _pyautogui: Injected or lazily imported pyautogui module.
        _pygetwindow: Injected or lazily imported pygetwindow module.
    """

    def __init__(
        self,
        *,
        pyautogui_module: Any | None = None,
        pygetwindow_module: Any | None = None,
    ) -> None:
        """Initialize the Windows adapter.

        Args:
            pyautogui_module: Optional pyautogui module for testing.
            pygetwindow_module: Optional pygetwindow module for testing.
        """
        self._pyautogui = pyautogui_module
        self._pygetwindow = pygetwindow_module

    @property
    def platform_name(self) -> str:
        """Return the platform identifier."""
        return "windows"

    @property
    def is_supported(self) -> bool:
        """Return True on Windows hosts."""
        return platform.system() == "Windows"

    async def health(self) -> bool:
        """Return True when required libraries import successfully."""
        if not self.is_supported:
            return False
        try:
            self._load_pyautogui()
            self._load_pygetwindow()
        except ImportError:
            return False
        return True

    async def focus_window(self, title: str) -> dict[str, Any]:
        """Focus a window matching ``title``."""
        return await asyncio.to_thread(self._focus_window_sync, title)

    async def click(
        self,
        x: int,
        y: int,
        *,
        button: str = "left",
    ) -> dict[str, Any]:
        """Click at screen coordinates."""
        return await asyncio.to_thread(self._click_sync, x, y, button)

    async def type_text(self, text: str, *, interval: float = 0.02) -> dict[str, Any]:
        """Type text at the current keyboard focus."""
        return await asyncio.to_thread(self._type_text_sync, text, interval)

    async def screenshot_region(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> dict[str, Any]:
        """Capture a screen region as base64 PNG."""
        return await asyncio.to_thread(
            self._screenshot_region_sync,
            x,
            y,
            width,
            height,
        )

    def _focus_window_sync(self, title: str) -> dict[str, Any]:
        """Synchronously focus a window by title substring."""
        gw = self._load_pygetwindow()
        matches = gw.getWindowsWithTitle(title)
        if not matches:
            msg = f"No window found matching title: {title}"
            raise DesktopAutomationError(msg)

        window = matches[0]
        try:
            window.activate()
        except Exception as exc:  # noqa: BLE001
            raise DesktopAutomationError(f"Failed to focus window: {exc}") from exc

        return {
            "matched_title": window.title,
            "focused": True,
        }

    def _click_sync(self, x: int, y: int, button: str) -> dict[str, Any]:
        """Synchronously perform a mouse click."""
        pyautogui = self._load_pyautogui()
        if button not in {"left", "right", "middle"}:
            msg = f"Unsupported mouse button: {button}"
            raise DesktopAutomationError(msg)

        pyautogui.click(x=x, y=y, button=button)
        return {"x": x, "y": y, "button": button, "clicked": True}

    def _type_text_sync(self, text: str, interval: float) -> dict[str, Any]:
        """Synchronously type text."""
        if not text:
            msg = "Text to type cannot be empty"
            raise DesktopAutomationError(msg)

        pyautogui = self._load_pyautogui()
        pyautogui.write(text, interval=interval)
        return {"typed": text, "length": len(text), "interval": interval}

    def _screenshot_region_sync(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> dict[str, Any]:
        """Synchronously capture a screen region."""
        if width <= 0 or height <= 0:
            msg = "Screenshot width and height must be positive"
            raise DesktopAutomationError(msg)

        pyautogui = self._load_pyautogui()
        image = pyautogui.screenshot(region=(x, y, width, height))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")

        return {
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "format": "png",
            "image_base64": encoded,
        }

    def _load_pyautogui(self) -> Any:
        """Load or return the pyautogui module."""
        if self._pyautogui is None:
            import pyautogui

            pyautogui.FAILSAFE = True
            self._pyautogui = pyautogui
        return self._pyautogui

    def _load_pygetwindow(self) -> Any:
        """Load or return the pygetwindow module."""
        if self._pygetwindow is None:
            import pygetwindow

            self._pygetwindow = pygetwindow
        return self._pygetwindow
