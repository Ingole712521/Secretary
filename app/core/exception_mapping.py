"""Map domain exceptions to HTTP status codes."""

from __future__ import annotations

from app.brain.exceptions import (
    ConversationNotFoundError,
    LLMCompletionError,
    LLMProviderError,
)
from app.exceptions import (
    AuthenticationException,
    ConfigurationException,
    JarvisError,
    ToolException,
    ValidationException,
)
from app.memory.exceptions import MemoryNotFoundError
from app.tools.exceptions import (
    ToolConfirmationRequiredError,
    ToolPermissionDeniedError,
    ToolValidationError,
)
from app.voice.exceptions import (
    SpeechToTextError,
    TextToSpeechError,
    VoiceNotAvailableError,
)

_STATUS_RESOLUTION_ORDER: list[tuple[type[JarvisError], int]] = [
    (ValidationException, 422),
    (ToolValidationError, 422),
    (ToolPermissionDeniedError, 403),
    (AuthenticationException, 401),
    (ConversationNotFoundError, 404),
    (MemoryNotFoundError, 404),
    (VoiceNotAvailableError, 503),
    (SpeechToTextError, 502),
    (TextToSpeechError, 502),
    (ToolConfirmationRequiredError, 428),
    (LLMCompletionError, 502),
    (LLMProviderError, 502),
    (ConfigurationException, 500),
    (ToolException, 500),
]


def resolve_status_code(exc: JarvisError) -> int:
    """Resolve the HTTP status code for a domain exception.

    Walks the exception type hierarchy so subclasses receive the
    correct status code from their parent type.

    Args:
        exc: Domain exception instance.

    Returns:
        HTTP status code.
    """
    for exc_type, status_code in _STATUS_RESOLUTION_ORDER:
        if isinstance(exc, exc_type):
            return status_code
    return 500
