"""Conversation and message schemas."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.utils.date import utc_now


class MessageRole(StrEnum):
    """Role of a participant in a conversation."""

    SYSTEM = "system"
    DEVELOPER = "developer"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Message(BaseModel):
    """A single message within a conversation.

    Attributes:
        id: Unique message identifier.
        role: Speaker role.
        content: Message text content.
        created_at: UTC timestamp when the message was created.
        metadata: Optional key-value metadata.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    role: MessageRole
    content: str
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Conversation(BaseModel):
    """A tracked conversation session.

    Attributes:
        id: Unique conversation identifier.
        title: Human-readable conversation title.
        messages: Ordered list of messages.
        metadata: Arbitrary conversation metadata.
        created_at: UTC creation timestamp.
        updated_at: UTC last-update timestamp.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str = Field(default="New Conversation")
    messages: list[Message] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def touch(self) -> None:
        """Update the conversation last-modified timestamp."""
        self.updated_at = utc_now()
