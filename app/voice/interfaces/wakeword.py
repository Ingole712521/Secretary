"""Wake word detection port."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Protocol

WakeWordCallback = Callable[[str, float], Awaitable[None] | None]


class WakeWordDetector(Protocol):
    """Port for wake word detection."""

    @property
    def provider_name(self) -> str:
        """Return the wake word provider identifier."""
        ...

    @property
    def wake_word(self) -> str:
        """Return the configured wake phrase."""
        ...

    async def health_check(self) -> bool:
        """Return True when wake word detection is available."""
        ...

    async def start(self, on_detected: WakeWordCallback) -> None:
        """Start listening for the wake word.

        Args:
            on_detected: Callback invoked with phrase and confidence.
        """
        ...

    async def stop(self) -> None:
        """Stop wake word detection."""
        ...
