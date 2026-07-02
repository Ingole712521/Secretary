"""Voice platform manager orchestrating the full voice pipeline."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import TYPE_CHECKING, Protocol

from app.constants import LOGGER_ROOT
from app.voice.events import VoiceEventBus, VoiceEventName
from app.voice.exceptions import VoiceError, VoiceNotAvailableError
from app.voice.manager.lifecycle import (
    assert_can_pause,
    assert_can_resume,
    assert_can_start,
    assert_can_stop,
)
from app.voice.schemas.models import VoiceLifecycleState
from app.voice.schemas.status import VoiceComponentStatus, VoicePlatformStatus

if TYPE_CHECKING:
    from app.voice.conversation.controller import ConversationController
    from app.voice.interfaces.audio_output import AudioOutput
    from app.voice.interfaces.microphone import Microphone
    from app.voice.interfaces.speech_to_text import SpeechToText
    from app.voice.interfaces.vad import VoiceActivityDetector
    from app.voice.interfaces.wakeword import WakeWordDetector

logger = logging.getLogger(f"{LOGGER_ROOT}.voice.manager")


class _HealthCheckable(Protocol):
    """Minimal protocol for voice component health reporting."""

    @property
    def provider_name(self) -> str: ...

    async def health_check(self) -> bool: ...


class VoiceManager:
    """Coordinates microphone capture through playback for Jarvis voice."""

    def __init__(
        self,
        *,
        enabled: bool,
        settings: object,
        microphone: Microphone,
        wake_word: WakeWordDetector,
        vad: VoiceActivityDetector,
        stt: SpeechToText,
        conversation: ConversationController,
        audio_output: AudioOutput,
        event_bus: VoiceEventBus,
        silence_timeout_ms: int,
    ) -> None:
        """Initialize the voice manager."""
        self._enabled = enabled
        self._settings = settings
        self._microphone = microphone
        self._wake_word = wake_word
        self._vad = vad
        self._stt = stt
        self._conversation = conversation
        self._audio_output = audio_output
        self._event_bus = event_bus
        self._silence_timeout_ms = silence_timeout_ms
        self._state = VoiceLifecycleState.IDLE
        self._last_error: str | None = None
        self._listen_task: asyncio.Task[None] | None = None
        self._capture_task: asyncio.Task[None] | None = None
        self._paused = False
        self._keepalive = asyncio.Event()

    @property
    def state(self) -> VoiceLifecycleState:
        """Return current lifecycle state."""
        return self._state

    async def initialize(self) -> None:
        """Validate component health without starting capture."""
        if not self._enabled:
            raise VoiceNotAvailableError("Voice interaction is disabled")
        self._state = VoiceLifecycleState.INITIALIZING
        healthy = await self._component_health()
        if not all(item.healthy for item in healthy):
            self._state = VoiceLifecycleState.ERROR
            raise VoiceNotAvailableError("One or more voice components are unavailable")
        self._state = VoiceLifecycleState.IDLE

    async def start(self) -> None:
        """Start wake word listening and voice lifecycle."""
        assert_can_start(self._state)
        if not self._enabled:
            raise VoiceNotAvailableError("Voice interaction is disabled")

        await self.initialize()
        self._state = VoiceLifecycleState.LISTENING
        self._paused = False
        self._keepalive = asyncio.Event()
        await self._microphone.start()
        await self._wake_word.start(self._on_wake_word_detected)
        self._listen_task = asyncio.create_task(self._idle_loop())
        await self._event_bus.emit(VoiceEventName.VOICE_STARTED)

    async def stop(self) -> None:
        """Stop voice capture and playback."""
        if self._state in {VoiceLifecycleState.IDLE, VoiceLifecycleState.STOPPED}:
            return
        assert_can_stop(self._state)
        self._state = VoiceLifecycleState.STOPPING
        self._keepalive.set()
        await self._cancel_tasks()
        await self._wake_word.stop()
        await self._microphone.stop()
        if hasattr(self._audio_output, "shutdown"):
            await self._audio_output.shutdown()
        self._state = VoiceLifecycleState.STOPPED
        await self._event_bus.emit(VoiceEventName.VOICE_STOPPED)

    async def pause(self) -> None:
        """Pause wake word listening."""
        assert_can_pause(self._state)
        self._paused = True
        self._state = VoiceLifecycleState.PAUSED

    async def resume(self) -> None:
        """Resume wake word listening."""
        assert_can_resume(self._state)
        self._paused = False
        self._state = VoiceLifecycleState.LISTENING

    async def shutdown(self) -> None:
        """Fully shutdown the voice manager."""
        await self.stop()

    async def get_status(self) -> VoicePlatformStatus:
        """Return aggregated platform status."""
        return VoicePlatformStatus(
            enabled=self._enabled,
            state=self._state,
            wake_word=self._wake_word.wake_word,
            language=getattr(self._settings, "voice_language", "en"),
            conversation_id=self._conversation.conversation_id,
            components=await self._component_health(),
            last_error=self._last_error,
        )

    async def process_audio_buffer(self, audio: bytes) -> None:
        """Process a buffered utterance without wake word (used in tests/API)."""
        await self._process_utterance(audio)

    async def _on_wake_word_detected(self, phrase: str, confidence: float) -> None:
        """Handle wake word detection."""
        if self._paused or self._state != VoiceLifecycleState.LISTENING:
            return
        await self._event_bus.emit(
            VoiceEventName.WAKE_WORD_DETECTED,
            phrase=phrase,
            confidence=confidence,
        )
        if self._capture_task is not None and not self._capture_task.done():
            return
        self._capture_task = asyncio.create_task(self._capture_utterance())

    async def _capture_utterance(self) -> None:
        """Capture speech until VAD reports end of utterance."""
        self._state = VoiceLifecycleState.PROCESSING
        await self._vad.reset()
        buffer = bytearray()
        async for chunk in self._microphone.stream():
            await self._event_bus.emit(VoiceEventName.SPEECH_DETECTED)
            buffer.extend(chunk)
            result = await self._vad.process_chunk(
                chunk,
                sample_rate=self._microphone.sample_rate,
            )
            if result.speech_ended:
                break
        await self._process_utterance(bytes(buffer))

    async def _process_utterance(self, audio: bytes) -> None:
        """Run STT → chat → TTS → playback for one utterance."""
        if not audio:
            self._state = VoiceLifecycleState.LISTENING
            return
        try:
            transcription = await self._stt.transcribe(
                audio,
                audio_format="pcm",
                sample_rate=self._microphone.sample_rate,
            )
            await self._event_bus.emit(
                VoiceEventName.SPEECH_RECOGNIZED,
                text=transcription.text,
                confidence=transcription.confidence,
            )
            turn = await self._conversation.handle_transcript(transcription.text)
            self._state = VoiceLifecycleState.SPEAKING
            await self._event_bus.emit(
                VoiceEventName.SPEECH_PLAYING,
                text=turn.response_text,
            )
            await self._audio_output.play(
                turn.synthesis.audio,
                audio_format=turn.synthesis.format,
                sample_rate=turn.synthesis.sample_rate,
            )
            await self._event_bus.emit(VoiceEventName.SPEECH_FINISHED)
        except VoiceError as exc:
            self._last_error = exc.message
            self._state = VoiceLifecycleState.ERROR
            await self._event_bus.emit(
                VoiceEventName.ERROR_OCCURRED,
                message=exc.message,
                code=exc.code,
            )
        finally:
            if self._state != VoiceLifecycleState.ERROR:
                self._state = VoiceLifecycleState.LISTENING

    async def _idle_loop(self) -> None:
        """Keep manager alive while listening."""
        await self._keepalive.wait()

    async def _cancel_tasks(self) -> None:
        """Cancel background tasks."""
        for task in (self._listen_task, self._capture_task):
            if task is not None and not task.done():
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
        self._listen_task = None
        self._capture_task = None

    async def _component_health(self) -> list[VoiceComponentStatus]:
        """Return health for all voice components."""
        components: list[tuple[str, _HealthCheckable]] = [
            ("microphone", self._microphone),
            ("wake_word", self._wake_word),
            ("vad", self._vad),
            ("stt", self._stt),
            ("tts", self._conversation.tts),
            ("audio_output", self._audio_output),
        ]
        statuses: list[VoiceComponentStatus] = []
        for name, component in components:
            healthy = await component.health_check()
            statuses.append(
                VoiceComponentStatus(
                    name=name,
                    provider=component.provider_name,
                    healthy=healthy,
                ),
            )
        return statuses
