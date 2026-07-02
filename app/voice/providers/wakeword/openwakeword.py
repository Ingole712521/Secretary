"""openWakeWord wake word detection provider."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import TYPE_CHECKING

from app.constants import LOGGER_ROOT
from app.voice.exceptions import WakeWordError
from app.voice.interfaces.wakeword import WakeWordCallback

if TYPE_CHECKING:
    from app.config.settings import Settings

logger = logging.getLogger(f"{LOGGER_ROOT}.voice.wakeword")


class OpenWakeWordDetector:
    """Wake word detection using the openWakeWord library."""

    def __init__(self, settings: Settings) -> None:
        """Initialize openWakeWord detector."""
        self._settings = settings
        self._model: object | None = None
        self._task: asyncio.Task[None] | None = None
        self._callback: WakeWordCallback | None = None
        self._running = False

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "openwakeword"

    @property
    def wake_word(self) -> str:
        """Return configured wake phrase."""
        return self._settings.voice_wake_word.lower()

    async def health_check(self) -> bool:
        """Return True when openwakeword is importable."""
        try:
            import openwakeword  # noqa: F401
        except ImportError:
            return False
        return True

    async def start(self, on_detected: WakeWordCallback) -> None:
        """Start background wake word detection."""
        self._callback = on_detected
        self._running = True
        self._task = asyncio.create_task(self._listen_loop())

    async def stop(self) -> None:
        """Stop wake word detection."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        self._callback = None

    async def _listen_loop(self) -> None:
        """Poll openWakeWord model until stopped."""
        try:
            model = await asyncio.to_thread(self._load_model)
        except ImportError as exc:
            raise WakeWordError("openwakeword is not installed") from exc

        while self._running:
            prediction = await asyncio.to_thread(self._predict, model)
            if prediction is not None and self._callback is not None:
                phrase, confidence = prediction
                result = self._callback(phrase, confidence)
                if asyncio.iscoroutine(result):
                    await result
            await asyncio.sleep(0.05)

    def _load_model(self) -> object:
        """Load openWakeWord model."""
        if self._model is not None:
            return self._model
        from openwakeword.model import Model

        self._model = Model(wakeword_models=[self._settings.voice_openwakeword_model])
        return self._model

    def _predict(self, model: object) -> tuple[str, float] | None:
        """Run a single wake word prediction."""
        scores = model.predict()  # type: ignore[attr-defined]
        for label, score in scores.items():
            if float(score) >= self._settings.voice_wake_word_threshold:
                return label.replace("_", " "), float(score)
        return None
