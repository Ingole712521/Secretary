"""Conversation API response models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class MessageItem(BaseModel):
    """A message within a conversation API response.

    Attributes:
        id: Unique message identifier.
        role: Speaker role.
        content: Message text.
        created_at: UTC creation timestamp.
    """

    id: str
    role: str
    content: str
    created_at: datetime


class ConversationSummary(BaseModel):
    """Summary of a conversation session.

    Attributes:
        id: Conversation identifier.
        title: Human-readable title.
        message_count: Number of messages in the session.
        created_at: UTC creation timestamp.
        updated_at: UTC last-update timestamp.
    """

    id: str
    title: str
    message_count: int
    created_at: datetime
    updated_at: datetime


class ConversationDetail(BaseModel):
    """Full conversation with message history.

    Attributes:
        id: Conversation identifier.
        title: Human-readable title.
        messages: Ordered message list.
        created_at: UTC creation timestamp.
        updated_at: UTC last-update timestamp.
    """

    id: str
    title: str
    messages: list[MessageItem] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
