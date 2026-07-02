"""Stub text-to-speech provider for tests."""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable

from app.voice.schemas.models import SynthesisOptions, SynthesisResult

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
        """Initialize the stub TTS provider."""
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

    async def synthesize(
        self,
        text: str,
        *,
        options: SynthesisOptions | None = None,
    ) -> SynthesisResult:
        """Return stub synthesized audio."""
        _ = options
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

    async def synthesize_stream(
        self,
        text: str,
        *,
        options: SynthesisOptions | None = None,
    ) -> AsyncIterator[bytes]:
        """Yield the full stub audio as one chunk."""
        result = await self.synthesize(text, options=options)
        yield result.audio
