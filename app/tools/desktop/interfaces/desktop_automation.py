"""Desktop automation port interface."""

from __future__ import annotations

from typing import Any, Protocol


class DesktopAutomation(Protocol):
    """Port for host desktop interaction (windows, input, screenshots).

    Implementations are platform-specific. Tools call these methods via
    ``asyncio.to_thread`` wrappers in adapters.
    """

    @property
    def platform_name(self) -> str:
        """Return the platform identifier (e.g. ``windows``)."""
        ...

    @property
    def is_supported(self) -> bool:
        """Return True when desktop automation is available on this host."""
        ...

    async def health(self) -> bool:
        """Return True when the adapter is operational."""
        ...

    async def focus_window(self, title: str) -> dict[str, Any]:
        """Bring a window whose title contains ``title`` to the foreground.

        Args:
            title: Substring matched against window titles.

        Returns:
            Structured result with matched window title.
        """
        ...

    async def click(
        self,
        x: int,
        y: int,
        *,
        button: str = "left",
    ) -> dict[str, Any]:
        """Click at screen coordinates.

        Args:
            x: Horizontal pixel coordinate.
            y: Vertical pixel coordinate.
            button: Mouse button (``left``, ``right``, ``middle``).

        Returns:
            Structured click result.
        """
        ...

    async def type_text(self, text: str, *, interval: float = 0.02) -> dict[str, Any]:
        """Type text using the keyboard.

        Args:
            text: Text to type.
            interval: Delay between keystrokes in seconds.

        Returns:
            Structured typing result.
        """
        ...

    async def screenshot_region(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> dict[str, Any]:
        """Capture a rectangular screen region.

        Args:
            x: Region left coordinate.
            y: Region top coordinate.
            width: Region width in pixels.
            height: Region height in pixels.

        Returns:
            Structured result including base64-encoded PNG data.
        """
        ...
