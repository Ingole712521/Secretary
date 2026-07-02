"""Voice domain schemas."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class VoiceLifecycleState(StrEnum):
    """Voice manager lifecycle states."""

    IDLE = "idle"
    INITIALIZING = "initializing"
    LISTENING = "listening"
    PAUSED = "paused"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class WordTimestamp(BaseModel):
    """Word-level transcription timestamp."""

    word: str
    start: float
    end: float
    confidence: float | None = None


class TranscriptionResult(BaseModel):
    """Result of a speech-to-text transcription."""

    text: str
    language: str | None = None
    provider: str = ""
    confidence: float | None = None
    words: list[WordTimestamp] = Field(default_factory=list)
    is_final: bool = True


class SynthesisOptions(BaseModel):
    """Optional text-to-speech synthesis parameters."""

    voice: str | None = None
    speed: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0
    language: str | None = None


class SynthesisResult(BaseModel):
    """Result of a text-to-speech synthesis."""

    audio: bytes
    format: str = "wav"
    provider: str = ""
    sample_rate: int | None = None


class VadResult(BaseModel):
    """Voice activity detection result for an audio chunk."""

    is_speech: bool = False
    speech_probability: float = 0.0
    speech_ended: bool = False


class VoiceTurnResult(BaseModel):
    """Full voice turn: transcript, chat reply, and reply audio."""

    transcript: str
    response_text: str
    conversation_id: str
    response_audio_base64: str
    audio_format: str = "wav"


class ConversationTurnResult(BaseModel):
    """Result of a conversation controller turn."""

    transcript: str
    response_text: str
    conversation_id: str
    synthesis: SynthesisResult
