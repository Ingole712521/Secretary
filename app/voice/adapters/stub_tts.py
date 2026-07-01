"""Stub text-to-speech adapter for tests."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from app.voice.schemas.models import SynthesisResult

SynthesisFn = Callable[[str], Awaitable[bytes] | bytes]


class StubTextToSpeech:
    """Returns configurable audio bytes without calling external APIs."""

    def __init__(
        self,
        *,
        audio: bytes = b"fake-audio",
        audio_format: str = "mp3",
        synthesize_fn: SynthesisFn | None = None,
    ) -> None:
        """Initialize the stub TTS adapter.

        Args:
            audio: Default audio bytes to return.
            audio_format: Audio format label.
            synthesize_fn: Optional override function.
        """
        self._audio = audio
        self._audio_format = audio_format
        self._synthesize_fn = synthesize_fn

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "stub"

    async def health_check(self) -> bool:
        """Stub TTS is always healthy."""
        return True

    async def synthesize(self, text: str) -> SynthesisResult:
        """Return stub synthesized audio."""
        if self._synthesize_fn is not None:
            result = self._synthesize_fn(text)
            audio = await result if hasattr(result, "__await__") else result
        else:
            audio = self._audio
        return SynthesisResult(
            audio=audio,
            format=self._audio_format,
            provider=self.provider_name,
        )
