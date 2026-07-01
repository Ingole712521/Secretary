"""Voice interaction application service."""

from __future__ import annotations

import base64
import logging
from typing import TYPE_CHECKING

from app.constants import LOGGER_ROOT
from app.exceptions import ConfigurationException
from app.models.chat import ChatRequest
from app.voice.exceptions import VoiceNotAvailableError
from app.voice.schemas.models import VoiceTurnResult

if TYPE_CHECKING:
    from app.config.settings import Settings
    from app.services.chat import ChatService
    from app.voice.interfaces.speech_to_text import SpeechToText
    from app.voice.interfaces.text_to_speech import TextToSpeech

logger = logging.getLogger(f"{LOGGER_ROOT}.voice")


class VoiceService:
    """Orchestrates voice turns: STT → chat → TTS.

    Attributes:
        _settings: Application settings.
        _chat_service: Chat completion service.
        _stt: Speech-to-text adapter.
        _tts: Text-to-speech adapter.
    """

    def __init__(
        self,
        settings: Settings,
        chat_service: ChatService,
        stt: SpeechToText,
        tts: TextToSpeech,
    ) -> None:
        """Initialize the voice service.

        Args:
            settings: Application settings.
            chat_service: Chat service for assistant replies.
            stt: Speech-to-text adapter.
            tts: Text-to-speech adapter.
        """
        self._settings = settings
        self._chat_service = chat_service
        self._stt = stt
        self._tts = tts

    @property
    def stt_provider_name(self) -> str:
        """Return the active STT provider name."""
        return self._stt.provider_name

    @property
    def tts_provider_name(self) -> str:
        """Return the active TTS provider name."""
        return self._tts.provider_name

    async def is_available(self) -> bool:
        """Return True when voice interaction is configured and healthy."""
        if not self._settings.voice_enabled:
            return False
        stt_ok = await self._stt.health_check()
        tts_ok = await self._tts.health_check()
        return stt_ok and tts_ok

    async def process_turn(
        self,
        audio: bytes,
        *,
        audio_format: str = "webm",
        conversation_id: str | None = None,
        enable_tools: bool = False,
        confirm: bool = False,
    ) -> VoiceTurnResult:
        """Process a complete voice turn.

        Args:
            audio: User speech audio bytes.
            audio_format: Audio format hint.
            conversation_id: Optional conversation session ID.
            enable_tools: Whether to allow tool calling in chat.
            confirm: Whether dangerous tools are confirmed.

        Returns:
            Transcript, assistant text, conversation ID, and reply audio.

        Raises:
            VoiceNotAvailableError: When voice is disabled or misconfigured.
        """
        if not self._settings.voice_enabled:
            raise VoiceNotAvailableError("Voice interaction is disabled")

        transcription = await self._stt.transcribe(audio, audio_format=audio_format)
        logger.info(
            "Voice transcript | provider=%s length=%d",
            transcription.provider,
            len(transcription.text),
        )

        try:
            chat_response = await self._chat_service.chat(
                ChatRequest(
                    message=transcription.text,
                    conversation_id=conversation_id,
                    enable_tools=enable_tools,
                    confirm=confirm,
                ),
            )
        except ConfigurationException as exc:
            raise VoiceNotAvailableError(str(exc.message)) from exc

        synthesis = await self._tts.synthesize(chat_response.message)
        encoded = base64.b64encode(synthesis.audio).decode("ascii")

        logger.info(
            "Voice turn complete | conversation=%s audio_bytes=%d",
            chat_response.conversation_id,
            len(synthesis.audio),
        )

        return VoiceTurnResult(
            transcript=transcription.text,
            response_text=chat_response.message,
            conversation_id=chat_response.conversation_id,
            response_audio_base64=encoded,
            audio_format=synthesis.format,
        )
