"""WebSocket voice session handler."""

from __future__ import annotations

import base64
import logging
from typing import TYPE_CHECKING

from fastapi import WebSocket, WebSocketDisconnect

from app.constants import LOGGER_ROOT
from app.exceptions.base import JarvisError
from app.voice.exceptions import VoiceError, VoiceNotAvailableError
from app.voice.schemas.protocol import (
    VoiceAudioMessage,
    VoiceAudioOutMessage,
    VoiceConfigMessage,
    VoiceEndTurnMessage,
    VoiceErrorMessage,
    VoiceReadyMessage,
    VoiceResponseMessage,
    VoiceTranscriptMessage,
    parse_client_message,
)

if TYPE_CHECKING:
    from app.services.voice import VoiceService

logger = logging.getLogger(f"{LOGGER_ROOT}.voice.session")


class VoiceSessionHandler:
    """Handles a single WebSocket voice session.

    Protocol:
        1. Server sends ``ready``
        2. Client sends ``config`` (optional ``conversation_id``)
        3. Client sends one or more ``audio`` messages
        4. Client sends ``end_turn``
        5. Server sends ``transcript``, ``response``, ``audio_out``

    Attributes:
        _voice_service: Voice orchestration service.
    """

    def __init__(self, voice_service: VoiceService) -> None:
        """Initialize the session handler.

        Args:
            voice_service: Voice service instance.
        """
        self._voice_service = voice_service

    async def handle(self, websocket: WebSocket) -> None:
        """Run the voice WebSocket session loop.

        Args:
            websocket: Connected WebSocket client.
        """
        await websocket.accept()

        stt_name = self._voice_service.stt_provider_name
        tts_name = self._voice_service.tts_provider_name
        available = await self._voice_service.is_available()

        await websocket.send_json(
            VoiceReadyMessage(
                voice_enabled=available,
                stt_provider=stt_name,
                tts_provider=tts_name,
            ).model_dump(),
        )

        conversation_id: str | None = None
        enable_tools = False
        confirm = False
        audio_buffer = bytearray()
        audio_format = "webm"

        try:
            while True:
                payload = await websocket.receive_json()
                message = parse_client_message(payload)

                if isinstance(message, VoiceConfigMessage):
                    conversation_id = message.conversation_id
                    enable_tools = message.enable_tools
                    confirm = message.confirm
                    continue

                if isinstance(message, VoiceAudioMessage):
                    audio_buffer.extend(base64.b64decode(message.data))
                    audio_format = message.format
                    continue

                if isinstance(message, VoiceEndTurnMessage):
                    await self._process_turn(
                        websocket,
                        bytes(audio_buffer),
                        audio_format=audio_format,
                        conversation_id=conversation_id,
                        enable_tools=enable_tools,
                        confirm=confirm,
                    )
                    audio_buffer.clear()
                    audio_format = "webm"
        except WebSocketDisconnect:
            logger.info("Voice WebSocket disconnected")
        except ValueError as exc:
            await self._send_error(websocket, str(exc), code="INVALID_MESSAGE")
        except VoiceError as exc:
            await self._send_error(websocket, exc.message, code=exc.code)
        except JarvisError as exc:
            await self._send_error(websocket, exc.message, code=exc.code)

    async def _process_turn(
        self,
        websocket: WebSocket,
        audio: bytes,
        *,
        audio_format: str,
        conversation_id: str | None,
        enable_tools: bool,
        confirm: bool,
    ) -> None:
        """Process one voice turn and stream results to the client."""
        if not audio:
            await self._send_error(
                websocket,
                "No audio received. Send audio messages before end_turn.",
                code="NO_AUDIO",
            )
            return

        try:
            result = await self._voice_service.process_turn(
                audio,
                audio_format=audio_format,
                conversation_id=conversation_id,
                enable_tools=enable_tools,
                confirm=confirm,
            )
        except VoiceNotAvailableError as exc:
            await self._send_error(websocket, exc.message, code=exc.code)
            return

        await websocket.send_json(
            VoiceTranscriptMessage(text=result.transcript).model_dump(),
        )
        await websocket.send_json(
            VoiceResponseMessage(
                text=result.response_text,
                conversation_id=result.conversation_id,
            ).model_dump(),
        )
        await websocket.send_json(
            VoiceAudioOutMessage(
                data=result.response_audio_base64,
                format=result.audio_format,
            ).model_dump(),
        )

    @staticmethod
    async def _send_error(
        websocket: WebSocket,
        message: str,
        *,
        code: str,
    ) -> None:
        """Send an error message to the client."""
        await websocket.send_json(
            VoiceErrorMessage(message=message, code=code).model_dump(),
        )
