"""WebSocket voice session protocol messages."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class VoiceMessageType(StrEnum):
    """Supported WebSocket voice message types."""

    CONFIG = "config"
    AUDIO = "audio"
    END_TURN = "end_turn"
    TRANSCRIPT = "transcript"
    RESPONSE = "response"
    AUDIO_OUT = "audio_out"
    ERROR = "error"
    READY = "ready"


class VoiceConfigMessage(BaseModel):
    """Client configuration for a voice session."""

    type: Literal["config"] = "config"
    conversation_id: str | None = None
    enable_tools: bool = False
    confirm: bool = False


class VoiceAudioMessage(BaseModel):
    """Client audio chunk message."""

    type: Literal["audio"] = "audio"
    data: str = Field(..., description="Base64-encoded audio bytes")
    format: str = Field(default="webm", description="Audio format hint")


class VoiceEndTurnMessage(BaseModel):
    """Signal that the user finished speaking."""

    type: Literal["end_turn"] = "end_turn"


class VoiceTranscriptMessage(BaseModel):
    """Server transcription result."""

    type: Literal["transcript"] = "transcript"
    text: str


class VoiceResponseMessage(BaseModel):
    """Server assistant text response."""

    type: Literal["response"] = "response"
    text: str
    conversation_id: str


class VoiceAudioOutMessage(BaseModel):
    """Server synthesized speech audio."""

    type: Literal["audio_out"] = "audio_out"
    data: str
    format: str = "mp3"


class VoiceErrorMessage(BaseModel):
    """Server error message."""

    type: Literal["error"] = "error"
    message: str
    code: str = "VOICE_ERROR"


class VoiceReadyMessage(BaseModel):
    """Server ready handshake."""

    type: Literal["ready"] = "ready"
    voice_enabled: bool = True
    stt_provider: str = ""
    tts_provider: str = ""


def parse_client_message(payload: dict[str, Any]) -> (
    VoiceConfigMessage | VoiceAudioMessage | VoiceEndTurnMessage
):
    """Parse an inbound client WebSocket message.

    Args:
        payload: Raw JSON object from the client.

    Returns:
        Parsed client message model.

    Raises:
        ValueError: When the message type is unknown or invalid.
    """
    message_type = payload.get("type")
    if message_type == VoiceMessageType.CONFIG:
        return VoiceConfigMessage.model_validate(payload)
    if message_type == VoiceMessageType.AUDIO:
        return VoiceAudioMessage.model_validate(payload)
    if message_type == VoiceMessageType.END_TURN:
        return VoiceEndTurnMessage.model_validate(payload)
    msg = f"Unsupported voice message type: {message_type}"
    raise ValueError(msg)
