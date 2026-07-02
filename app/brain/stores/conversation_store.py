"""In-memory conversation store implementation.

Sprint 2 uses process-local storage only. This is conversation
session tracking, not long-term semantic memory.
"""

from __future__ import annotations

from app.brain.exceptions import ConversationNotFoundError
from app.brain.schemas.conversation import Conversation, Message


class InMemoryConversationStore:
    """Process-local conversation store implementing ``ConversationStore``."""

    def __init__(self) -> None:
        """Initialize an empty in-memory store."""
        self._conversations: dict[str, Conversation] = {}

    async def create(
        self,
        title: str = "New Conversation",
        *,
        conversation_id: str | None = None,
    ) -> Conversation:
        """Create a new conversation.

        Args:
            title: Optional conversation title.
            conversation_id: Optional explicit identifier to assign. Used to
                recreate a conversation whose ID a client still references
                after the process-local store was reset.

        Returns:
            Newly created conversation.
        """
        conversation = (
            Conversation(title=title)
            if conversation_id is None
            else Conversation(id=conversation_id, title=title)
        )
        self._conversations[conversation.id] = conversation
        return conversation

    async def get(self, conversation_id: str) -> Conversation | None:
        """Retrieve a conversation by ID.

        Args:
            conversation_id: Conversation identifier.

        Returns:
            Conversation if found, otherwise None.
        """
        return self._conversations.get(conversation_id)

    async def save(self, conversation: Conversation) -> Conversation:
        """Persist conversation changes.

        Args:
            conversation: Conversation to save.

        Returns:
            Saved conversation.
        """
        conversation.touch()
        self._conversations[conversation.id] = conversation
        return conversation

    async def add_message(
        self,
        conversation_id: str,
        message: Message,
    ) -> Conversation:
        """Append a message to a conversation.

        Args:
            conversation_id: Target conversation ID.
            message: Message to append.

        Returns:
            Updated conversation.

        Raises:
            ConversationNotFoundError: If the conversation does not exist.
        """
        conversation = self._conversations.get(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError(conversation_id)
        conversation.messages.append(message)
        conversation.touch()
        return conversation

    async def list_conversations(self) -> list[Conversation]:
        """List all stored conversations.

        Returns:
            List of conversations.
        """
        return list(self._conversations.values())
