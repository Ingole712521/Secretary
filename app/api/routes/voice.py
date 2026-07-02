"""Voice API routes."""

from __future__ import annotations

import base64

from fastapi import APIRouter, WebSocket

from app.dependencies import ContainerDep, VoicePlatformServiceDep, VoiceServiceDep
from app.models.voice import (
    VoiceActionResponse,
    VoiceStatusResponse,
    VoiceSynthesizeRequest,
    VoiceSynthesizeResponse,
)
from app.voice.session_handler import VoiceSessionHandler

router = APIRouter(prefix="/voice", tags=["Voice"])


@router.post("/synthesize", response_model=VoiceSynthesizeResponse)
async def synthesize_speech(
    request: VoiceSynthesizeRequest,
    container: ContainerDep,
) -> VoiceSynthesizeResponse:
    """Synthesize speech using the configured free Edge TTS provider."""
    result = await container.voice_platform.tts.synthesize(request.text)
    return VoiceSynthesizeResponse(
        audio_base64=base64.b64encode(result.audio).decode("ascii"),
        format=result.format,
    )


@router.post("/start", response_model=VoiceActionResponse)
async def start_voice(
    voice_platform_service: VoicePlatformServiceDep,
) -> VoiceActionResponse:
    """Start local voice listening (wake word → speech → reply)."""
    status = await voice_platform_service.start()
    return VoiceActionResponse(status=status)


@router.post("/stop", response_model=VoiceActionResponse)
async def stop_voice(
    voice_platform_service: VoicePlatformServiceDep,
) -> VoiceActionResponse:
    """Stop local voice listening and playback."""
    status = await voice_platform_service.stop()
    return VoiceActionResponse(status=status)


@router.get("/status", response_model=VoiceStatusResponse)
async def voice_status(
    voice_platform_service: VoicePlatformServiceDep,
) -> VoiceStatusResponse:
    """Return voice platform status and component health."""
    status = await voice_platform_service.status()
    return VoiceStatusResponse(status=status)


@router.websocket("/ws")
async def voice_websocket(
    websocket: WebSocket,
    voice_service: VoiceServiceDep,
) -> None:
    """Real-time voice session: speak → transcript → Jarvis reply → audio."""
    handler = VoiceSessionHandler(voice_service)
    await handler.handle(websocket)
