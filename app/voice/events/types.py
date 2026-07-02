"""Voice platform event type definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class VoiceEventName(StrEnum):
    """Published voice lifecycle and pipeline events."""

    VOICE_STARTED = "voice_started"
    VOICE_STOPPED = "voice_stopped"
    WAKE_WORD_DETECTED = "wake_word_detected"
    SPEECH_DETECTED = "speech_detected"
    SPEECH_RECOGNIZED = "speech_recognized"
    LLM_REQUEST_STARTED = "llm_request_started"
    LLM_RESPONSE_RECEIVED = "llm_response_received"
    SPEECH_PLAYING = "speech_playing"
    SPEECH_FINISHED = "speech_finished"
    ERROR_OCCURRED = "error_occurred"


@dataclass(frozen=True, slots=True)
class VoiceEvent:
    """Immutable voice event published on the event bus.

    Attributes:
        name: Event identifier.
        timestamp: UTC time when the event was created.
        payload: Optional structured event data.
    """

    name: VoiceEventName
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any] = field(default_factory=dict)
