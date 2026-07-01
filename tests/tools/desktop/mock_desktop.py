"""Mock desktop automation adapter for tests."""

from __future__ import annotations

from typing import Any


class MockDesktopAutomation:
    """In-memory mock implementing the desktop automation port."""

    def __init__(self, *, supported: bool = True) -> None:
        """Initialize mock state."""
        self.focused: list[str] = []
        self.clicks: list[dict[str, Any]] = []
        self.typed: list[str] = []
        self.screenshots: list[dict[str, int]] = []
        self._supported = supported

    @property
    def platform_name(self) -> str:
        """Return mock platform name."""
        return "mock"

    @property
    def is_supported(self) -> bool:
        """Return configured support flag."""
        return self._supported

    async def health(self) -> bool:
        """Return support flag as health."""
        return self._supported

    async def focus_window(self, title: str) -> dict[str, Any]:
        """Record a focus action."""
        self.focused.append(title)
        return {"matched_title": title, "focused": True}

    async def click(
        self,
        x: int,
        y: int,
        *,
        button: str = "left",
    ) -> dict[str, Any]:
        """Record a click action."""
        payload = {"x": x, "y": y, "button": button, "clicked": True}
        self.clicks.append(payload)
        return payload

    async def type_text(self, text: str, *, interval: float = 0.02) -> dict[str, Any]:
        """Record typed text."""
        self.typed.append(text)
        return {"typed": text, "length": len(text), "interval": interval}

    async def screenshot_region(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> dict[str, Any]:
        """Record a screenshot request."""
        payload = {
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "format": "png",
            "image_base64": "aGVsbG8=",
        }
        self.screenshots.append({"x": x, "y": y, "width": width, "height": height})
        return payload
