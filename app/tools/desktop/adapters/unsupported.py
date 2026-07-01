"""Unsupported platform desktop automation stub."""

from __future__ import annotations

import platform
from typing import Any

from app.tools.desktop.exceptions import DesktopAutomationError


class UnsupportedDesktopAutomation:
    """Graceful stub when desktop automation is unavailable.

    Returns clear errors instead of crashing on unsupported platforms.
    """

    @property
    def platform_name(self) -> str:
        """Return the detected OS platform name."""
        return platform.system().lower()

    @property
    def is_supported(self) -> bool:
        """Desktop automation is not supported on this stub."""
        return False

    async def health(self) -> bool:
        """Unsupported adapters are never healthy."""
        return False

    async def focus_window(self, title: str) -> dict[str, Any]:
        """Raise because desktop automation is unsupported."""
        _ = title
        raise DesktopAutomationError(self._unsupported_message())

    async def click(
        self,
        x: int,
        y: int,
        *,
        button: str = "left",
    ) -> dict[str, Any]:
        """Raise because desktop automation is unsupported."""
        _ = x, y, button
        raise DesktopAutomationError(self._unsupported_message())

    async def type_text(self, text: str, *, interval: float = 0.02) -> dict[str, Any]:
        """Raise because desktop automation is unsupported."""
        _ = text, interval
        raise DesktopAutomationError(self._unsupported_message())

    async def screenshot_region(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> dict[str, Any]:
        """Raise because desktop automation is unsupported."""
        _ = x, y, width, height
        raise DesktopAutomationError(self._unsupported_message())

    def _unsupported_message(self) -> str:
        """Build a platform-aware unsupported error message."""
        return (
            f"Desktop automation is not supported on {self.platform_name}. "
            "Windows is the primary supported platform."
        )
