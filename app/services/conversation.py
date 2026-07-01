"""Conversation session application service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.brain.schemas.conversation import Conversation, Message
from app.models.conversation import ConversationDetail, ConversationSummary, MessageItem

if TYPE_CHECKING:
    from app.brain.conversation_manager import ConversationManager


class ConversationService:
    """Exposes conversation session data for the API layer.

    Attributes:
        _conversation_manager: Brain conversation lifecycle manager.
    """

    def __init__(self, conversation_manager: ConversationManager) -> None:
        """Initialize the conversation service.

        Args:
            conversation_manager: Conversation tracking component.
        """
        self._conversation_manager = conversation_manager

    async def list_conversations(self) -> list[ConversationSummary]:
        """List all conversation sessions.

        Returns:
            Conversation summaries ordered by most recently updated first.
        """
        conversations = await self._conversation_manager.list_conversations()
        conversations.sort(key=lambda item: item.updated_at, reverse=True)
        return [_to_summary(conversation) for conversation in conversations]

    async def get_conversation(self, conversation_id: str) -> ConversationDetail:
        """Return a conversation with full message history.

        Args:
            conversation_id: Conversation identifier.

        Returns:
            Conversation detail including messages.

        Raises:
            ConversationNotFoundError: If the conversation does not exist.
        """
        messages = await self._conversation_manager.get_history(conversation_id)
        conversation = await self._conversation_manager.get_or_create(conversation_id)
        return _to_detail(conversation, messages)


def _to_summary(conversation: Conversation) -> ConversationSummary:
    """Map a domain conversation to an API summary."""
    return ConversationSummary(
        id=conversation.id,
        title=conversation.title,
        message_count=len(conversation.messages),
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


def _to_detail(
    conversation: Conversation,
    messages: list[Message],
) -> ConversationDetail:
    """Map a domain conversation to an API detail response."""
    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        messages=[
            MessageItem(
                id=message.id,
                role=message.role.value,
                content=message.content,
                created_at=message.created_at,
            )
            for message in messages
        ],
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )
