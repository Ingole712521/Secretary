"""LLM tool-calling schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LLMToolCall(BaseModel):
    """A tool invocation requested by the language model.

    Attributes:
        id: Provider-assigned tool call identifier.
        name: Function name as returned by the provider.
        arguments: Parsed tool arguments.
    """

    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class LLMToolDefinition(BaseModel):
    """OpenAI-compatible function tool definition for LLM requests.

    Attributes:
        name: Function name exposed to the model.
        description: What the function does.
        parameters: JSON Schema object for function parameters.
    """

    name: str
    description: str
    parameters: dict[str, Any] = Field(default_factory=dict)
