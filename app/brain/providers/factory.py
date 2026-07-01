"""LLM provider registration helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.brain.providers.openrouter import OpenRouterProvider
from app.brain.schemas.llm import LLMProviderName
from app.config.settings import LLMProviderSetting

if TYPE_CHECKING:
    from app.brain.model_router import ModelRouter
    from app.config.settings import Settings


def register_llm_providers(
    settings: Settings,
    model_router: ModelRouter,
) -> OpenRouterProvider | None:
    """Register concrete LLM provider adapters on the model router.

    Args:
        settings: Application settings.
        model_router: Model router to receive provider registrations.

    Returns:
        OpenRouter provider instance when registered, otherwise None.
    """
    openrouter_provider: OpenRouterProvider | None = None

    if settings.llm_provider == LLMProviderSetting.OPENROUTER:
        openrouter_provider = OpenRouterProvider(settings)
        model_router.register_provider(
            LLMProviderName.OPENROUTER,
            openrouter_provider,
        )

    return openrouter_provider
