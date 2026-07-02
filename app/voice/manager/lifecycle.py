"""Voice manager lifecycle helpers."""

from __future__ import annotations

from app.voice.exceptions import VoiceLifecycleError
from app.voice.schemas.models import VoiceLifecycleState

_STARTABLE_STATES = {
    VoiceLifecycleState.IDLE,
    VoiceLifecycleState.STOPPED,
    VoiceLifecycleState.ERROR,
}
_STOPPABLE_STATES = {
    VoiceLifecycleState.LISTENING,
    VoiceLifecycleState.PAUSED,
    VoiceLifecycleState.PROCESSING,
    VoiceLifecycleState.SPEAKING,
    VoiceLifecycleState.INITIALIZING,
}
_PAUSABLE_STATES = {VoiceLifecycleState.LISTENING}
_RESUMABLE_STATES = {VoiceLifecycleState.PAUSED}


def assert_can_start(state: VoiceLifecycleState) -> None:
    """Raise when start is not allowed from the current state."""
    if state not in _STARTABLE_STATES:
        raise VoiceLifecycleError(f"Cannot start voice from state '{state.value}'")


def assert_can_stop(state: VoiceLifecycleState) -> None:
    """Raise when stop is not allowed from the current state."""
    if state not in _STOPPABLE_STATES:
        raise VoiceLifecycleError(f"Cannot stop voice from state '{state.value}'")


def assert_can_pause(state: VoiceLifecycleState) -> None:
    """Raise when pause is not allowed from the current state."""
    if state not in _PAUSABLE_STATES:
        raise VoiceLifecycleError(f"Cannot pause voice from state '{state.value}'")


def assert_can_resume(state: VoiceLifecycleState) -> None:
    """Raise when resume is not allowed from the current state."""
    if state not in _RESUMABLE_STATES:
        raise VoiceLifecycleError(f"Cannot resume voice from state '{state.value}'")
