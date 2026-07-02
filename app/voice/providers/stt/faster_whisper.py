"""Faster Whisper local speech-to-text provider."""

from __future__ import annotations

import asyncio
import logging
import tempfile
from collections.abc import AsyncIterator
from pathlib import Path
from typing import TYPE_CHECKING

from app.constants import LOGGER_ROOT
from app.voice.exceptions import SpeechToTextError
from app.voice.schemas.models import TranscriptionResult, WordTimestamp
from app.voice.utils.audio import pcm_to_wav

if TYPE_CHECKING:
    from app.config.settings import Settings

logger = logging.getLogger(f"{LOGGER_ROOT}.voice.stt.faster_whisper")


class FasterWhisperStt:
    """Local Faster Whisper STT provider with configurable model and device."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the Faster Whisper provider."""
        self._settings = settings
        self._model: object | None = None

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "faster_whisper"

    async def health_check(self) -> bool:
        """Return True when faster-whisper is importable."""
        try:
            import faster_whisper  # noqa: F401
        except ImportError:
            return False
        return True

    async def transcribe(
        self,
        audio: bytes,
        *,
        audio_format: str = "wav",
        language: str | None = None,
        sample_rate: int | None = None,
    ) -> TranscriptionResult:
        """Transcribe audio using Faster Whisper."""
        if not audio:
            raise SpeechToTextError("Audio payload is empty")

        audio_path = await asyncio.to_thread(
            self._write_temp_audio,
            audio,
            audio_format=audio_format,
            sample_rate=sample_rate or self._settings.voice_sample_rate,
        )
        try:
            return await asyncio.to_thread(
                self._transcribe_file,
                audio_path,
                language=language or self._settings.voice_language,
            )
        finally:
            path = Path(audio_path)
            await asyncio.to_thread(path.unlink, missing_ok=True)

    async def transcribe_stream(
        self,
        audio: bytes,
        *,
        audio_format: str = "wav",
        language: str | None = None,
        sample_rate: int | None = None,
    ) -> AsyncIterator[TranscriptionResult]:
        """Yield the final Faster Whisper transcription."""
        yield await self.transcribe(
            audio,
            audio_format=audio_format,
            language=language,
            sample_rate=sample_rate,
        )

    def _get_model(self) -> object:
        """Load and cache the Whisper model."""
        if self._model is not None:
            return self._model
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise SpeechToTextError("faster-whisper is not installed") from exc

        self._model = WhisperModel(
            self._settings.voice_whisper_model,
            device=self._settings.voice_whisper_device,
            compute_type=self._settings.voice_whisper_compute_type,
        )
        return self._model

    def _write_temp_audio(
        self,
        audio: bytes,
        *,
        audio_format: str,
        sample_rate: int,
    ) -> str:
        """Persist audio bytes to a temporary file for transcription."""
        suffix = f".{audio_format.lower()}"
        if audio_format.lower() == "pcm":
            audio = pcm_to_wav(audio, sample_rate=sample_rate)
            suffix = ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
            handle.write(audio)
            return handle.name

    def _transcribe_file(
        self,
        audio_path: str,
        *,
        language: str,
    ) -> TranscriptionResult:
        """Synchronously transcribe an audio file."""
        model = self._get_model()
        segments, info = model.transcribe(  # type: ignore[attr-defined]
            audio_path,
            language=language,
            word_timestamps=True,
        )
        words: list[WordTimestamp] = []
        text_parts: list[str] = []
        for segment in segments:
            text_parts.append(segment.text.strip())
            if segment.words:
                for word in segment.words:
                    words.append(
                        WordTimestamp(
                            word=word.word.strip(),
                            start=word.start,
                            end=word.end,
                            confidence=getattr(word, "probability", None),
                        ),
                    )
        text = " ".join(part for part in text_parts if part).strip()
        if not text:
            raise SpeechToTextError("Faster Whisper returned an empty transcript")

        logger.info("Faster Whisper transcription success | length=%d", len(text))
        return TranscriptionResult(
            text=text,
            language=getattr(info, "language", language),
            provider=self.provider_name,
            confidence=getattr(info, "language_probability", None),
            words=words,
        )
