"""Chat API request and response models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request payload for the chat completion endpoint.

    Attributes:
        message: User message text.
        system_prompt: Optional system instruction prepended to the request.
        model: Optional model override; defaults to the configured provider model.
        temperature: Sampling temperature for the completion.
        max_tokens: Maximum tokens to generate, if set.
    """

    message: str = Field(
        ...,
        min_length=1,
        max_length=32_000,
        description="User message to send to the model",
    )
    system_prompt: str | None = Field(
        default=None,
        max_length=16_000,
        description="Optional system instruction",
    )
    model: str | None = Field(
        default=None,
        max_length=256,
        description="Optional model override",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature",
    )
    max_tokens: int | None = Field(
        default=None,
        ge=1,
        le=128_000,
        description="Maximum tokens to generate",
    )


class ChatResponse(BaseModel):
    """Response payload from the chat completion endpoint.

    Attributes:
        message: Assistant reply text.
        model: Model identifier that produced the response.
        provider: LLM provider identifier.
        finish_reason: Provider-specific completion reason.
        usage: Token usage statistics when reported by the provider.
    """

    message: str = Field(..., description="Assistant response text")
    model: str = Field(..., description="Model that generated the response")
    provider: str = Field(..., description="LLM provider identifier")
    finish_reason: str | None = Field(
        default=None,
        description="Provider completion reason",
    )
    usage: dict[str, int] = Field(
        default_factory=dict,
        description="Token usage statistics",
    )
