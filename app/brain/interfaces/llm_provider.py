"""LLM provider port interface.

Concrete adapters (OpenAI, Anthropic, etc.) will implement this
protocol in future sprints. Sprint 2 defines the contract only.
"""

from __future__ import annotations

from typing import Protocol

from app.brain.schemas.llm import LLMRequest, LLMResponse, ModelInfo


class LLMProvider(Protocol):
    """Port for language model inference providers.

    Implementations must not be added in Sprint 2. This interface
    defines the contract for future provider adapters.
    """

    @property
    def provider_name(self) -> str:
        """Return the provider identifier."""
        ...

    async def list_models(self) -> list[ModelInfo]:
        """List models available from this provider.

        Returns:
            List of model metadata objects.
        """
        ...

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Generate a completion for the given request.

        Args:
            request: Structured LLM request payload.

        Returns:
            Structured LLM response.
        """
        ...

    async def health_check(self) -> bool:
        """Check whether the provider is reachable.

        Returns:
            True if the provider is healthy.
        """
        ...
