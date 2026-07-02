"""Conversation store port interface."""

from __future__ import annotations

from typing import Protocol

from app.brain.schemas.conversation import Conversation, Message


class ConversationStore(Protocol):
    """Port for persisting and retrieving conversations.

    Sprint 2 uses in-memory implementations only. Database adapters
    will implement this protocol in a future sprint.
    """

    async def create(
        self,
        title: str = "New Conversation",
        *,
        conversation_id: str | None = None,
    ) -> Conversation:
        """Create a new conversation.

        Args:
            title: Optional conversation title.
            conversation_id: Optional explicit identifier to assign.

        Returns:
            Newly created conversation.
        """
        ...

    async def get(self, conversation_id: str) -> Conversation | None:
        """Retrieve a conversation by ID.

        Args:
            conversation_id: Conversation identifier.

        Returns:
            Conversation if found, otherwise None.
        """
        ...

    async def save(self, conversation: Conversation) -> Conversation:
        """Persist conversation changes.

        Args:
            conversation: Conversation to save.

        Returns:
            Saved conversation.
        """
        ...

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
        """
        ...

    async def list_conversations(self) -> list[Conversation]:
        """List all stored conversations.

        Returns:
            List of conversations.
        """
        ...
