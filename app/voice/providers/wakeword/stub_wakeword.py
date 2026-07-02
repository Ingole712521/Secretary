"""Stub wake word detection provider."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from app.voice.interfaces.wakeword import WakeWordCallback

WakeWordTriggerFn = Callable[[], Awaitable[None] | None]


class StubWakeWordDetector:
    """Test double wake word detector with manual trigger support."""

    def __init__(self, *, wake_word: str = "hey jarvis") -> None:
        """Initialize the stub wake word detector."""
        self._wake_word = wake_word.lower()
        self._callback: WakeWordCallback | None = None
        self._running = False

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "stub"

    @property
    def wake_word(self) -> str:
        """Return configured wake phrase."""
        return self._wake_word

    async def health_check(self) -> bool:
        """Stub wake word detector is always healthy."""
        return True

    async def start(self, on_detected: WakeWordCallback) -> None:
        """Store callback for manual triggering."""
        self._callback = on_detected
        self._running = True

    async def stop(self) -> None:
        """Stop wake word detection."""
        self._running = False
        self._callback = None

    async def trigger(self, *, confidence: float = 0.99) -> None:
        """Manually trigger wake word detection in tests."""
        if not self._running or self._callback is None:
            return
        result = self._callback(self._wake_word, confidence)
        if asyncio.iscoroutine(result):
            await result
