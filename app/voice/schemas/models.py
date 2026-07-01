"""Voice domain schemas."""

from __future__ import annotations

from pydantic import BaseModel


class TranscriptionResult(BaseModel):
    """Result of a speech-to-text transcription.

    Attributes:
        text: Transcribed text.
        language: Detected or configured language code.
        provider: STT provider identifier.
    """

    text: str
    language: str | None = None
    provider: str = ""


class SynthesisResult(BaseModel):
    """Result of a text-to-speech synthesis.

    Attributes:
        audio: Raw audio bytes.
        format: Audio container/codec (mp3, wav).
        provider: TTS provider identifier.
    """

    audio: bytes
    format: str = "mp3"
    provider: str = ""


class VoiceTurnResult(BaseModel):
    """Full voice turn: transcript, chat reply, and reply audio.

    Attributes:
        transcript: User speech transcription.
        response_text: Assistant reply text.
        conversation_id: Active conversation session ID.
        response_audio_base64: Base64-encoded reply audio.
        audio_format: Reply audio format.
    """

    transcript: str
    response_text: str
    conversation_id: str
    response_audio_base64: str
    audio_format: str = "mp3"
