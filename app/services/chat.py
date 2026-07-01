"""Chat completion application service."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.brain.schemas.conversation import Message, MessageRole
from app.brain.schemas.llm import LLMProviderName, LLMRequest
from app.constants import LOGGER_CHAT
from app.exceptions import ConfigurationException
from app.models.chat import ChatRequest, ChatResponse
from app.services.base import BaseService

if TYPE_CHECKING:
    from app.brain.model_router import ModelRouter
    from app.config.settings import Settings


logger = logging.getLogger(LOGGER_CHAT)


class ChatService(BaseService):
    """Orchestrates user chat requests through the LLM provider layer.

    Accepts a user message, routes it to the configured provider via
    ``ModelRouter``, and returns a structured assistant response.

    Attributes:
        _model_router: Model selection and provider resolution.
    """

    def __init__(self, settings: Settings, model_router: ModelRouter) -> None:
        """Initialize the chat service.

        Args:
            settings: Application configuration.
            model_router: Model router with registered provider adapters.
        """
        super().__init__(settings)
        self._model_router = model_router

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Send a user message to the configured LLM provider.

        Args:
            request: Validated chat request payload.

        Returns:
            Structured assistant response.

        Raises:
            ConfigurationException: When LLM credentials are not configured.
            ModelRoutingError: When the provider adapter is not registered.
            LLMProviderError: When the provider request fails.
            LLMCompletionError: When the provider returns an error response.
        """
        if not self._settings.has_llm_credentials:
            msg = (
                f"LLM API key is not configured for provider "
                f"'{self._settings.llm_provider.value}'"
            )
            raise ConfigurationException(msg)

        provider_name = LLMProviderName(self._settings.llm_provider.value)
        provider = self._model_router.get_provider(provider_name)
        model_id = request.model or self._settings.get_active_llm_model()
        model_info = self._model_router.select_model(
            provider=provider_name,
            model_id=model_id,
        )

        messages: list[Message] = []
        if request.system_prompt:
            messages.append(
                Message(role=MessageRole.SYSTEM, content=request.system_prompt),
            )
        messages.append(Message(role=MessageRole.USER, content=request.message))

        llm_request = LLMRequest(
            model=model_info,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        logger.info(
            "Chat request | provider=%s model=%s message_length=%d",
            provider_name.value,
            model_id,
            len(request.message),
        )

        llm_response = await provider.complete(llm_request)

        logger.info(
            "Chat response | provider=%s model=%s finish_reason=%s",
            provider_name.value,
            llm_response.model.model_id,
            llm_response.finish_reason,
        )

        return ChatResponse(
            message=llm_response.content,
            model=llm_response.model.model_id,
            provider=provider_name.value,
            finish_reason=llm_response.finish_reason,
            usage=llm_response.usage,
        )
