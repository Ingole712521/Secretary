"""Stub speech-to-text provider for tests."""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable

from app.voice.schemas.models import TranscriptionResult, WordTimestamp

TranscriptionFn = Callable[[bytes, str], Awaitable[str] | str]


class StubSpeechToText:
    """Returns configurable transcripts without calling external APIs."""

    def __init__(
        self,
        *,
        transcript: str = "hello jarvis",
        confidence: float = 0.99,
        transcribe_fn: TranscriptionFn | None = None,
    ) -> None:
        """Initialize the stub STT provider."""
        self._transcript = transcript
        self._confidence = confidence
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
        audio_format: str = "wav",
        language: str | None = None,
        sample_rate: int | None = None,
    ) -> TranscriptionResult:
        """Return a stub transcription."""
        _ = language, sample_rate
        if self._transcribe_fn is not None:
            result = self._transcribe_fn(audio, audio_format)
            text = await result if hasattr(result, "__await__") else result
        else:
            text = self._transcript
        return TranscriptionResult(
            text=text,
            provider=self.provider_name,
            confidence=self._confidence,
            words=[
                WordTimestamp(
                    word=text,
                    start=0.0,
                    end=1.0,
                    confidence=self._confidence,
                ),
            ],
        )

    async def transcribe_stream(
        self,
        audio: bytes,
        *,
        audio_format: str = "wav",
        language: str | None = None,
        sample_rate: int | None = None,
    ) -> AsyncIterator[TranscriptionResult]:
        """Yield a single final stub transcription."""
        yield await self.transcribe(
            audio,
            audio_format=audio_format,
            language=language,
            sample_rate=sample_rate,
        )
