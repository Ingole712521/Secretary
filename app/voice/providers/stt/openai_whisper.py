"""OpenAI Whisper cloud speech-to-text provider."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

import httpx

from app.config.settings import Settings
from app.constants import LOGGER_ROOT
from app.voice.exceptions import SpeechToTextError, VoiceNotAvailableError
from app.voice.schemas.models import TranscriptionResult

logger = logging.getLogger(f"{LOGGER_ROOT}.voice.stt.openai")

_DEFAULT_TIMEOUT = httpx.Timeout(60.0, connect=10.0)

_FORMAT_TO_MIME: dict[str, str] = {
    "webm": "audio/webm",
    "wav": "audio/wav",
    "mp3": "audio/mpeg",
    "ogg": "audio/ogg",
    "m4a": "audio/mp4",
}


class OpenAiWhisperStt:
    """OpenAI Whisper API adapter for speech-to-text."""

    def __init__(
        self,
        settings: Settings,
        *,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize the Whisper STT provider."""
        self._settings = settings
        self._http_client = http_client

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "openai_whisper"

    async def health_check(self) -> bool:
        """Return True when an OpenAI STT API key is configured."""
        return self._settings.get_voice_stt_api_key() is not None

    async def transcribe(
        self,
        audio: bytes,
        *,
        audio_format: str = "webm",
        language: str | None = None,
        sample_rate: int | None = None,
    ) -> TranscriptionResult:
        """Transcribe audio using OpenAI Whisper."""
        _ = sample_rate
        api_key = self._require_api_key()
        if not audio:
            raise SpeechToTextError("Audio payload is empty")

        url = f"{self._api_base()}/audio/transcriptions"
        mime = _FORMAT_TO_MIME.get(audio_format.lower(), "application/octet-stream")
        filename = f"audio.{audio_format.lower()}"
        data: dict[str, str] = {"model": self._settings.openai_whisper_model}
        if language:
            data["language"] = language
        files = {"file": (filename, audio, mime)}

        try:
            client = await self._get_client()
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {api_key}"},
                data=data,
                files=files,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text or str(exc.response.status_code)
            logger.error("Whisper STT HTTP error: %s", detail)
            raise SpeechToTextError(f"Whisper transcription failed: {detail}") from exc
        except httpx.HTTPError as exc:
            raise SpeechToTextError(f"Whisper request failed: {exc}") from exc

        payload = response.json()
        text = str(payload.get("text", "")).strip()
        if not text:
            raise SpeechToTextError("Whisper returned an empty transcript")

        return TranscriptionResult(
            text=text,
            language=language,
            provider=self.provider_name,
        )

    async def transcribe_stream(
        self,
        audio: bytes,
        *,
        audio_format: str = "webm",
        language: str | None = None,
        sample_rate: int | None = None,
    ) -> AsyncIterator[TranscriptionResult]:
        """Yield the final OpenAI Whisper transcription."""
        yield await self.transcribe(
            audio,
            audio_format=audio_format,
            language=language,
            sample_rate=sample_rate,
        )

    def _require_api_key(self) -> str:
        """Return OpenAI STT API key or raise."""
        api_key = self._settings.get_voice_stt_api_key()
        if api_key is None:
            msg = (
                "OpenAI API key required for Whisper STT. "
                "Set OPENAI_API_KEY to a direct OpenAI key."
            )
            raise VoiceNotAvailableError(msg)
        return api_key.get_secret_value()

    def _api_base(self) -> str:
        """Return OpenAI API base URL without trailing slash."""
        base = self._settings.openai_api_base or "https://api.openai.com/v1"
        return base.rstrip("/")

    async def _get_client(self) -> httpx.AsyncClient:
        """Return injected or owned HTTP client."""
        if self._http_client is not None:
            return self._http_client
        return httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT)
