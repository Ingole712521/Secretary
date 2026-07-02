"""OpenAI text-to-speech provider."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

import httpx

from app.config.settings import Settings
from app.constants import LOGGER_ROOT
from app.voice.exceptions import TextToSpeechError, VoiceNotAvailableError
from app.voice.schemas.models import SynthesisOptions, SynthesisResult

logger = logging.getLogger(f"{LOGGER_ROOT}.voice.tts.openai")

_DEFAULT_TIMEOUT = httpx.Timeout(60.0, connect=10.0)


class OpenAiTts:
    """OpenAI TTS API provider."""

    def __init__(
        self,
        settings: Settings,
        *,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize the OpenAI TTS provider."""
        self._settings = settings
        self._http_client = http_client

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "openai_tts"

    async def health_check(self) -> bool:
        """Return True when an OpenAI API key is configured."""
        return self._settings.get_voice_stt_api_key() is not None

    async def synthesize(
        self,
        text: str,
        *,
        options: SynthesisOptions | None = None,
    ) -> SynthesisResult:
        """Synthesize speech using OpenAI TTS."""
        if not text.strip():
            raise TextToSpeechError("Cannot synthesize empty text")

        api_key = self._require_api_key()
        voice = (
            options.voice
            if options and options.voice
            else self._settings.openai_tts_voice
        )
        url = f"{self._api_base()}/audio/speech"
        payload = {
            "model": self._settings.openai_tts_model,
            "input": text,
            "voice": voice,
        }
        try:
            client = await self._get_client()
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text or str(exc.response.status_code)
            raise TextToSpeechError(f"OpenAI TTS failed: {detail}") from exc
        except httpx.HTTPError as exc:
            raise TextToSpeechError(f"OpenAI TTS request failed: {exc}") from exc

        return SynthesisResult(
            audio=response.content,
            format="mp3",
            provider=self.provider_name,
        )

    async def synthesize_stream(
        self,
        text: str,
        *,
        options: SynthesisOptions | None = None,
    ) -> AsyncIterator[bytes]:
        """Yield the full OpenAI TTS response as one chunk."""
        result = await self.synthesize(text, options=options)
        yield result.audio

    def _require_api_key(self) -> str:
        """Return OpenAI API key or raise."""
        api_key = self._settings.get_voice_stt_api_key()
        if api_key is None:
            raise VoiceNotAvailableError("OpenAI API key required for OpenAI TTS")
        return api_key.get_secret_value()

    def _api_base(self) -> str:
        """Return OpenAI API base URL."""
        base = self._settings.openai_api_base or "https://api.openai.com/v1"
        return base.rstrip("/")

    async def _get_client(self) -> httpx.AsyncClient:
        """Return injected or owned HTTP client."""
        if self._http_client is not None:
            return self._http_client
        return httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT)
