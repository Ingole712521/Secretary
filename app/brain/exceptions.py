"""Brain-specific exceptions."""

from __future__ import annotations

from app.exceptions.base import JarvisError


class BrainError(JarvisError):
    """Base exception for Brain subsystem errors."""

    def __init__(self, message: str, *, code: str = "BRAIN_ERROR") -> None:
        """Initialize a Brain error.

        Args:
            message: Human-readable error description.
            code: Machine-readable error code.
        """
        super().__init__(message, code=code)


class ConversationNotFoundError(BrainError):
    """Raised when a conversation ID does not exist."""

    def __init__(self, conversation_id: str) -> None:
        """Initialize with the missing conversation ID.

        Args:
            conversation_id: Identifier that was not found.
        """
        super().__init__(
            f"Conversation not found: {conversation_id}",
            code="CONVERSATION_NOT_FOUND",
        )
        self.conversation_id = conversation_id


class PlanGenerationError(BrainError):
    """Raised when plan generation fails."""

    def __init__(self, message: str) -> None:
        """Initialize a plan generation error.

        Args:
            message: Description of the failure.
        """
        super().__init__(message, code="PLAN_GENERATION_ERROR")


class ModelRoutingError(BrainError):
    """Raised when no suitable model can be selected."""

    def __init__(self, message: str) -> None:
        """Initialize a model routing error.

        Args:
            message: Description of the routing failure.
        """
        super().__init__(message, code="MODEL_ROUTING_ERROR")


class PromptNotFoundError(BrainError):
    """Raised when a requested prompt template is missing."""

    def __init__(self, name: str) -> None:
        """Initialize with the missing prompt name.

        Args:
            name: Template name that was not found.
        """
        super().__init__(
            f"Prompt template not found: {name}",
            code="PROMPT_NOT_FOUND",
        )
        self.prompt_name = name
