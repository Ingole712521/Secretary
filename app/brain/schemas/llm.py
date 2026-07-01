"""LLM request and response schemas."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.brain.schemas.conversation import Message


class LLMProviderName(StrEnum):
    """Supported LLM provider identifiers.

    Providers are defined as interfaces only in Sprint 2.
    Concrete adapters will be implemented in later sprints.
    """

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    DEEPSEEK = "deepseek"
    OLLAMA = "ollama"
    LM_STUDIO = "lm_studio"


class ModelCapability(StrEnum):
    """Capabilities supported by a language model."""

    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    VISION = "vision"
    FUNCTION_CALLING = "function_calling"
    STREAMING = "streaming"


class ModelInfo(BaseModel):
    """Metadata describing an available language model.

    Attributes:
        provider: Provider identifier.
        model_id: Provider-specific model name.
        display_name: Human-readable model name.
        capabilities: Supported model capabilities.
        context_window: Maximum context tokens, if known.
        metadata: Provider-specific metadata.
    """

    provider: LLMProviderName
    model_id: str
    display_name: str
    capabilities: list[ModelCapability] = Field(default_factory=list)
    context_window: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMRequest(BaseModel):
    """Request payload for an LLM provider adapter.

    Attributes:
        model: Target model metadata.
        messages: Conversation messages for the request.
        temperature: Sampling temperature.
        max_tokens: Maximum tokens to generate.
        stream: Whether to stream the response.
        metadata: Optional request metadata.
    """

    model: ModelInfo
    messages: list[Message]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = None
    stream: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    """Response payload from an LLM provider adapter.

    Attributes:
        content: Generated text content.
        model: Model that produced the response.
        finish_reason: Provider-specific completion reason.
        usage: Token usage statistics.
        metadata: Optional response metadata.
    """

    content: str
    model: ModelInfo
    finish_reason: str | None = None
    usage: dict[str, int] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
