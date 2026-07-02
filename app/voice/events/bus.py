"""Voice event bus for decoupled platform notifications."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from app.constants import LOGGER_ROOT
from app.voice.events.types import VoiceEvent, VoiceEventName

if TYPE_CHECKING:
    pass

logger = logging.getLogger(f"{LOGGER_ROOT}.voice.events")

VoiceEventHandler = Callable[[VoiceEvent], Awaitable[None] | None]


class VoiceEventBus:
    """Simple async publish/subscribe bus for voice events.

    Attributes:
        _handlers: Registered async or sync event handlers.
    """

    def __init__(self) -> None:
        """Initialize an empty event bus."""
        self._handlers: dict[VoiceEventName, list[VoiceEventHandler]] = {}
        self._global_handlers: list[VoiceEventHandler] = []

    def subscribe(
        self,
        event_name: VoiceEventName | None,
        handler: VoiceEventHandler,
    ) -> None:
        """Register a handler for a specific event or all events.

        Args:
            event_name: Event to listen for, or ``None`` for all events.
            handler: Callable invoked when the event is published.
        """
        if event_name is None:
            self._global_handlers.append(handler)
            return
        self._handlers.setdefault(event_name, []).append(handler)

    async def publish(self, event: VoiceEvent) -> None:
        """Publish an event to all matching subscribers.

        Args:
            event: Voice event to dispatch.
        """
        handlers = list(self._global_handlers)
        handlers.extend(self._handlers.get(event.name, []))
        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                logger.exception("Voice event handler failed | event=%s", event.name)

    async def emit(
        self,
        name: VoiceEventName,
        **payload: object,
    ) -> None:
        """Create and publish an event with a payload.

        Args:
            name: Event name.
            **payload: Structured event data.
        """
        await self.publish(
            VoiceEvent(name=name, payload=dict(payload)),
        )
