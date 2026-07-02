"""Voice conversation controller."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.constants import LOGGER_ROOT
from app.exceptions import ConfigurationException
from app.models.chat import ChatRequest
from app.voice.events import VoiceEventBus, VoiceEventName
from app.voice.exceptions import VoiceNotAvailableError
from app.voice.schemas.models import ConversationTurnResult, SynthesisOptions

if TYPE_CHECKING:
    from app.config.settings import Settings
    from app.services.chat import ChatService
    from app.voice.interfaces.text_to_speech import TextToSpeech

logger = logging.getLogger(f"{LOGGER_ROOT}.voice.conversation")


class ConversationController:
    """Bridges recognized speech to chat and synthesized responses."""

    def __init__(
        self,
        settings: Settings,
        chat_service: ChatService,
        tts: TextToSpeech,
        event_bus: VoiceEventBus,
    ) -> None:
        """Initialize conversation controller."""
        self._settings = settings
        self._chat_service = chat_service
        self._tts = tts
        self._event_bus = event_bus
        self._conversation_id: str | None = None

    @property
    def conversation_id(self) -> str | None:
        """Return the active conversation identifier."""
        return self._conversation_id

    @property
    def tts(self) -> TextToSpeech:
        """Return the configured TTS provider."""
        return self._tts

    def set_conversation_id(self, conversation_id: str | None) -> None:
        """Set the active conversation session."""
        self._conversation_id = conversation_id

    async def handle_transcript(
        self,
        transcript: str,
        *,
        enable_tools: bool | None = None,
        confirm: bool = False,
    ) -> ConversationTurnResult:
        """Send transcript to chat and synthesize the assistant reply.

        Args:
            transcript: Recognized user speech.
            enable_tools: Whether tool calling is enabled.
            confirm: Whether dangerous tools are confirmed.

        Returns:
            Conversation turn with text and synthesized audio.
        """
        if not transcript.strip():
            raise VoiceNotAvailableError("Transcript is empty")

        await self._event_bus.emit(
            VoiceEventName.LLM_REQUEST_STARTED,
            transcript=transcript,
        )

        tools_enabled = (
            enable_tools if enable_tools is not None else self._settings.tools_enabled
        )
        try:
            chat_response = await self._chat_service.chat(
                ChatRequest(
                    message=transcript,
                    conversation_id=self._conversation_id,
                    enable_tools=tools_enabled,
                    confirm=confirm,
                ),
            )
        except ConfigurationException as exc:
            raise VoiceNotAvailableError(str(exc.message)) from exc

        self._conversation_id = chat_response.conversation_id
        await self._event_bus.emit(
            VoiceEventName.LLM_RESPONSE_RECEIVED,
            response=chat_response.message,
            conversation_id=chat_response.conversation_id,
        )

        synthesis = await self._tts.synthesize(
            chat_response.message,
            options=SynthesisOptions(
                voice=self._settings.voice_piper_voice,
                speed=self._settings.voice_piper_speed,
                pitch=self._settings.voice_piper_pitch,
                volume=self._settings.voice_piper_volume,
            ),
        )

        logger.info(
            "Conversation turn complete | conversation=%s",
            chat_response.conversation_id,
        )
        return ConversationTurnResult(
            transcript=transcript,
            response_text=chat_response.message,
            conversation_id=chat_response.conversation_id,
            synthesis=synthesis,
        )
