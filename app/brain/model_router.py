"""Model selection and provider routing (interfaces only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from app.brain.exceptions import ModelRoutingError
from app.brain.interfaces.llm_provider import LLMProvider
from app.brain.schemas.llm import (
    LLMProviderName,
    ModelCapability,
    ModelInfo,
)

if TYPE_CHECKING:
    pass

# Registry of known models per provider — metadata only, no connections.
_PROVIDER_MODELS: dict[LLMProviderName, list[ModelInfo]] = {
    LLMProviderName.OPENAI: [
        ModelInfo(
            provider=LLMProviderName.OPENAI,
            model_id="gpt-4o",
            display_name="GPT-4o",
            capabilities=[
                ModelCapability.CHAT,
                ModelCapability.VISION,
                ModelCapability.STREAMING,
            ],
            context_window=128_000,
        ),
    ],
    LLMProviderName.ANTHROPIC: [
        ModelInfo(
            provider=LLMProviderName.ANTHROPIC,
            model_id="claude-sonnet-4-20250514",
            display_name="Claude Sonnet",
            capabilities=[ModelCapability.CHAT, ModelCapability.STREAMING],
            context_window=200_000,
        ),
    ],
    LLMProviderName.GEMINI: [
        ModelInfo(
            provider=LLMProviderName.GEMINI,
            model_id="gemini-2.0-flash",
            display_name="Gemini 2.0 Flash",
            capabilities=[ModelCapability.CHAT, ModelCapability.VISION],
            context_window=1_000_000,
        ),
    ],
    LLMProviderName.OPENROUTER: [
        ModelInfo(
            provider=LLMProviderName.OPENROUTER,
            model_id="openrouter/auto",
            display_name="OpenRouter Auto",
            capabilities=[ModelCapability.CHAT],
        ),
    ],
    LLMProviderName.DEEPSEEK: [
        ModelInfo(
            provider=LLMProviderName.DEEPSEEK,
            model_id="deepseek-chat",
            display_name="DeepSeek Chat",
            capabilities=[ModelCapability.CHAT],
            context_window=64_000,
        ),
    ],
    LLMProviderName.OLLAMA: [
        ModelInfo(
            provider=LLMProviderName.OLLAMA,
            model_id="llama3",
            display_name="Llama 3 (Local)",
            capabilities=[ModelCapability.CHAT],
        ),
    ],
    LLMProviderName.LM_STUDIO: [
        ModelInfo(
            provider=LLMProviderName.LM_STUDIO,
            model_id="local-model",
            display_name="LM Studio Local",
            capabilities=[ModelCapability.CHAT, ModelCapability.COMPLETION],
        ),
    ],
}


@dataclass
class ModelRouter:
    """Selects models and resolves provider adapters.

    Sprint 2 registers provider interfaces only. No network calls are
    made. ``select_model`` returns metadata; ``get_provider`` raises
    until a concrete adapter is registered in a future sprint.

    Attributes:
        default_provider: Preferred provider when none is specified.
        _providers: Registered provider adapter instances.
    """

    default_provider: LLMProviderName = LLMProviderName.OPENAI
    _providers: dict[LLMProviderName, LLMProvider] = field(default_factory=dict)

    def register_provider(
        self,
        provider_name: LLMProviderName,
        provider: LLMProvider,
    ) -> None:
        """Register a concrete provider adapter.

        Args:
            provider_name: Provider identifier.
            provider: Adapter implementing ``LLMProvider``.

        Note:
            No providers are registered in Sprint 2.
        """
        self._providers[provider_name] = provider

    def list_providers(self) -> list[LLMProviderName]:
        """List all known provider identifiers.

        Returns:
            Provider names from the metadata registry.
        """
        return list(_PROVIDER_MODELS.keys())

    def list_models(
        self,
        provider: LLMProviderName | None = None,
    ) -> list[ModelInfo]:
        """List available model metadata.

        Args:
            provider: Optional provider filter.

        Returns:
            Model metadata entries. No provider APIs are called.
        """
        if provider is not None:
            return list(_PROVIDER_MODELS.get(provider, []))
        models: list[ModelInfo] = []
        for provider_models in _PROVIDER_MODELS.values():
            models.extend(provider_models)
        return models

    def select_model(
        self,
        *,
        provider: LLMProviderName | None = None,
        model_id: str | None = None,
        required_capabilities: list[ModelCapability] | None = None,
    ) -> ModelInfo:
        """Select a model based on provider and capability requirements.

        Args:
            provider: Preferred provider. Defaults to ``default_provider``.
            model_id: Specific model ID. Uses first match if omitted.
            required_capabilities: Capabilities the model must support.

        Returns:
            Selected model metadata.

        Raises:
            ModelRoutingError: If no suitable model is found.
        """
        chosen_provider = provider or self.default_provider
        candidates = self.list_models(chosen_provider)
        if not candidates:
            msg = f"No models registered for provider: {chosen_provider}"
            raise ModelRoutingError(msg)

        if required_capabilities:
            candidates = [
                m
                for m in candidates
                if all(cap in m.capabilities for cap in required_capabilities)
            ]

        if model_id is not None:
            matched = [m for m in candidates if m.model_id == model_id]
            if not matched:
                msg = f"Model '{model_id}' not found for provider '{chosen_provider}'"
                raise ModelRoutingError(msg)
            return matched[0]

        if not candidates:
            msg = "No model satisfies the required capabilities"
            raise ModelRoutingError(msg)
        return candidates[0]

    def get_provider(self, provider: LLMProviderName) -> LLMProvider:
        """Return a registered provider adapter.

        Args:
            provider: Provider identifier.

        Returns:
            Registered provider adapter.

        Raises:
            ModelRoutingError: If no adapter is registered.
        """
        adapter = self._providers.get(provider)
        if adapter is None:
            msg = (
                f"Provider '{provider}' is not registered. "
                "Sprint 2 defines interfaces only — implement adapters later."
            )
            raise ModelRoutingError(msg)
        return adapter
