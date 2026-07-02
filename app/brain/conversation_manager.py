"""Conversation lifecycle management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.brain.exceptions import ConversationNotFoundError
from app.brain.schemas.conversation import Conversation, Message, MessageRole

if TYPE_CHECKING:
    from app.brain.interfaces.conversation_store import ConversationStore


class ConversationManager:
    """Manages conversation sessions, messages, and metadata.

    Architecture layer between the Orchestrator and ``ConversationStore``.
    Does not perform LLM calls or plan execution.

    Attributes:
        _store: Conversation persistence port.
    """

    def __init__(self, store: ConversationStore) -> None:
        """Initialize with a conversation store adapter.

        Args:
            store: Conversation persistence port implementation.
        """
        self._store = store

    async def get_or_create(
        self,
        conversation_id: str | None = None,
        *,
        title: str = "New Conversation",
    ) -> Conversation:
        """Retrieve an existing conversation or create a new one.

        Args:
            conversation_id: Optional existing conversation ID.
            title: Title for newly created conversations.

        Returns:
            Active conversation instance.
        """
        if conversation_id is not None:
            existing = await self._store.get(conversation_id)
            if existing is not None:
                return existing
            # The process-local store may have been reset (e.g. server
            # reload) while a client still holds the ID. Recreate the
            # conversation under the same ID instead of failing.
            return await self._store.create(
                title=title,
                conversation_id=conversation_id,
            )
        return await self._store.create(title=title)

    async def add_user_message(
        self,
        conversation_id: str,
        content: str,
    ) -> Conversation:
        """Append a user message to a conversation.

        Args:
            conversation_id: Target conversation ID.
            content: User message text.

        Returns:
            Updated conversation.
        """
        message = Message(role=MessageRole.USER, content=content)
        return await self._store.add_message(conversation_id, message)

    async def add_assistant_message(
        self,
        conversation_id: str,
        content: str,
    ) -> Conversation:
        """Append an assistant message to a conversation.

        Args:
            conversation_id: Target conversation ID.
            content: Assistant message text.

        Returns:
            Updated conversation.
        """
        message = Message(role=MessageRole.ASSISTANT, content=content)
        return await self._store.add_message(conversation_id, message)

    async def add_message(
        self,
        conversation_id: str,
        message: Message,
    ) -> Conversation:
        """Append any message to a conversation.

        Args:
            conversation_id: Target conversation ID.
            message: Message to append.

        Returns:
            Updated conversation.
        """
        return await self._store.add_message(conversation_id, message)

    async def get_history(self, conversation_id: str) -> list[Message]:
        """Return message history for a conversation.

        Args:
            conversation_id: Conversation identifier.

        Returns:
            Ordered message list.

        Raises:
            ConversationNotFoundError: If the conversation does not exist.
        """
        conversation = await self._store.get(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError(conversation_id)
        return list(conversation.messages)

    async def update_metadata(
        self,
        conversation_id: str,
        metadata: dict[str, object],
    ) -> Conversation:
        """Merge metadata into a conversation.

        Args:
            conversation_id: Conversation identifier.
            metadata: Metadata key-value pairs to merge.

        Returns:
            Updated conversation.

        Raises:
            ConversationNotFoundError: If the conversation does not exist.
        """
        conversation = await self._store.get(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError(conversation_id)
        conversation.metadata.update(metadata)
        return await self._store.save(conversation)

    async def list_conversations(self) -> list[Conversation]:
        """List all tracked conversations.

        Returns:
            All conversations in the store.
        """
        return await self._store.list_conversations()
