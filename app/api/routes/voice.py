"""Voice WebSocket API routes."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket

from app.dependencies import VoiceServiceDep
from app.voice.session_handler import VoiceSessionHandler

router = APIRouter(prefix="/voice", tags=["Voice"])


@router.websocket("/ws")
async def voice_websocket(
    websocket: WebSocket,
    voice_service: VoiceServiceDep,
) -> None:
    """Real-time voice session: speak → transcript → Jarvis reply → audio."""
    handler = VoiceSessionHandler(voice_service)
    await handler.handle(websocket)
