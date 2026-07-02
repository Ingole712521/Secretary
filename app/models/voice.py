"""Voice API models."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.voice.schemas.status import VoicePlatformStatus


class VoiceSynthesizeRequest(BaseModel):
    """Request to synthesize speech from text."""

    text: str = Field(..., min_length=1, max_length=8000)


class VoiceSynthesizeResponse(BaseModel):
    """Synthesized speech audio response."""

    audio_base64: str
    format: str = "mp3"


class VoiceActionResponse(BaseModel):
    """Response from voice start/stop actions."""

    status: VoicePlatformStatus = Field(..., description="Voice platform status")


class VoiceStatusResponse(BaseModel):
    """Response from voice status endpoint."""

    status: VoicePlatformStatus = Field(..., description="Voice platform status")
