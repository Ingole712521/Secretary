"""Execution context schema."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.brain.schemas.conversation import Conversation
from app.brain.schemas.prompt import Prompt


class ExecutionContext(BaseModel):
    """Merged context prepared for planning and LLM requests.

      Aggregates conversation history, prompts, session data, and
    placeholders for future memory and environment integrations.

      Attributes:
          conversation: Active conversation, if any.
          system_prompts: Resolved system-level prompts.
          session: Ephemeral session key-value data.
          environment: Deployment/runtime environment metadata.
          memory: Placeholder for future long-term memory entries.
          metadata: Additional context metadata.
    """

    conversation: Conversation | None = None
    system_prompts: list[Prompt] = Field(default_factory=list)
    session: dict[str, Any] = Field(default_factory=dict)
    environment: dict[str, Any] = Field(default_factory=dict)
    memory: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
