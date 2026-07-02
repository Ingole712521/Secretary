"""Voice platform status schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.voice.schemas.models import VoiceLifecycleState


class VoiceComponentStatus(BaseModel):
    """Health status for a single voice component."""

    name: str
    provider: str
    healthy: bool


class VoicePlatformStatus(BaseModel):
    """Aggregated voice platform status."""

    enabled: bool
    state: VoiceLifecycleState
    wake_word: str
    language: str
    conversation_id: str | None = None
    components: list[VoiceComponentStatus] = Field(default_factory=list)
    last_error: str | None = None
