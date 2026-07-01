"""Prompt management schemas."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.utils.date import utc_now


class PromptType(StrEnum):
    """Category of prompt used in the Brain pipeline."""

    SYSTEM = "system"
    DEVELOPER = "developer"
    USER = "user"
    TOOL = "tool"
    SAFETY = "safety"


class PromptVersion(BaseModel):
    """Version metadata for a prompt template.

    Attributes:
        version: Semantic version string.
        created_at: UTC timestamp when this version was registered.
        changelog: Optional description of changes.
    """

    version: str
    created_at: datetime = Field(default_factory=utc_now)
    changelog: str = ""


class PromptTemplate(BaseModel):
    """Reusable prompt template with variable placeholders.

    Attributes:
        id: Unique template identifier.
        name: Human-readable template name.
        prompt_type: Prompt category.
        template: Template string with ``{variable}`` placeholders.
        variables: Declared variable names.
        version: Active version metadata.
        metadata: Optional template metadata.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    prompt_type: PromptType
    template: str
    variables: list[str] = Field(default_factory=list)
    version: PromptVersion = Field(
        default_factory=lambda: PromptVersion(version="1.0.0"),
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class Prompt(BaseModel):
    """Resolved prompt ready for LLM consumption.

    Attributes:
        id: Unique prompt identifier.
        prompt_type: Prompt category.
        content: Fully resolved prompt text.
        source_template_id: Originating template ID, if any.
        version: Version string of the resolved prompt.
        metadata: Optional prompt metadata.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    prompt_type: PromptType
    content: str
    source_template_id: str | None = None
    version: str = "1.0.0"
    metadata: dict[str, Any] = Field(default_factory=dict)
