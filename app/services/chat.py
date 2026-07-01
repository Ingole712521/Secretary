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
    from app.brain.conversation_manager import ConversationManager
    from app.brain.model_router import ModelRouter
    from app.config.settings import Settings


logger = logging.getLogger(LOGGER_CHAT)


class ChatService(BaseService):
    """Orchestrates multi-turn chat through the LLM provider layer.

    Persists user and assistant messages in a conversation session so
    Jarvis remembers context across turns.

    Attributes:
        _model_router: Model selection and provider resolution.
        _conversation_manager: Conversation session tracking.
    """

    def __init__(
        self,
        settings: Settings,
        model_router: ModelRouter,
        conversation_manager: ConversationManager,
    ) -> None:
        """Initialize the chat service.

        Args:
            settings: Application configuration.
            model_router: Model router with registered provider adapters.
            conversation_manager: Conversation lifecycle manager.
        """
        super().__init__(settings)
        self._model_router = model_router
        self._conversation_manager = conversation_manager

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Send a user message and return an assistant reply.

        Creates a new conversation when ``conversation_id`` is omitted.
        Prior messages in the session are included in the LLM request.

        Args:
            request: Validated chat request payload.

        Returns:
            Structured assistant response with conversation ID.

        Raises:
            ConfigurationException: When LLM credentials are not configured.
            ConversationNotFoundError: When an unknown conversation ID is given.
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

        conversation = await self._conversation_manager.get_or_create(
            request.conversation_id,
        )
        await self._conversation_manager.add_user_message(
            conversation.id,
            request.message,
        )

        provider_name = LLMProviderName(self._settings.llm_provider.value)
        provider = self._model_router.get_provider(provider_name)
        model_id = request.model or self._settings.get_active_llm_model()
        model_info = self._model_router.select_model(
            provider=provider_name,
            model_id=model_id,
        )

        messages = await self._build_llm_messages(
            conversation_id=conversation.id,
            system_prompt=request.system_prompt,
        )

        llm_request = LLMRequest(
            model=model_info,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        logger.info(
            "Chat request | conversation=%s provider=%s model=%s turns=%d",
            conversation.id,
            provider_name.value,
            model_id,
            len(messages),
        )

        llm_response = await provider.complete(llm_request)

        await self._conversation_manager.add_assistant_message(
            conversation.id,
            llm_response.content,
        )

        logger.info(
            "Chat response | conversation=%s model=%s finish_reason=%s",
            conversation.id,
            llm_response.model.model_id,
            llm_response.finish_reason,
        )

        return ChatResponse(
            message=llm_response.content,
            conversation_id=conversation.id,
            model=llm_response.model.model_id,
            provider=provider_name.value,
            finish_reason=llm_response.finish_reason,
            usage=llm_response.usage,
        )

    async def _build_llm_messages(
        self,
        *,
        conversation_id: str,
        system_prompt: str | None,
    ) -> list[Message]:
        """Build the message list sent to the LLM provider.

        Args:
            conversation_id: Active conversation identifier.
            system_prompt: Optional per-request system instruction override.

        Returns:
            Messages in provider order: system (if any), then session history.
        """
        history = await self._conversation_manager.get_history(conversation_id)
        messages: list[Message] = []

        effective_system = system_prompt or self._settings.jarvis_system_prompt
        if effective_system:
            messages.append(
                Message(role=MessageRole.SYSTEM, content=effective_system),
            )

        messages.extend(history)
        return messages
