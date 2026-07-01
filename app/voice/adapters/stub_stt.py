"""Stub speech-to-text adapter for tests."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from app.voice.schemas.models import TranscriptionResult

TranscriptionFn = Callable[[bytes, str], Awaitable[str] | str]


class StubSpeechToText:
    """Returns configurable transcripts without calling external APIs."""

    def __init__(
        self,
        *,
        transcript: str = "hello jarvis",
        transcribe_fn: TranscriptionFn | None = None,
    ) -> None:
        """Initialize the stub STT adapter.

        Args:
            transcript: Default transcript text.
            transcribe_fn: Optional override function.
        """
        self._transcript = transcript
        self._transcribe_fn = transcribe_fn

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "stub"

    async def health_check(self) -> bool:
        """Stub STT is always healthy."""
        return True

    async def transcribe(
        self,
        audio: bytes,
        *,
        audio_format: str = "webm",
        language: str | None = None,
    ) -> TranscriptionResult:
        """Return a stub transcription."""
        _ = language
        if self._transcribe_fn is not None:
            result = self._transcribe_fn(audio, audio_format)
            text = await result if hasattr(result, "__await__") else result
        else:
            text = self._transcript
        return TranscriptionResult(text=text, provider=self.provider_name)
