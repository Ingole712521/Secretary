"""Chat completion application service."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.brain.schemas.conversation import Message, MessageRole
from app.brain.schemas.llm import LLMProviderName, LLMRequest
from app.constants import LOGGER_CHAT
from app.exceptions import ConfigurationException
from app.models.chat import ChatRequest, ChatResponse, ToolInvocationSummary
from app.services.base import BaseService
from app.tools.exceptions import ToolConfirmationRequiredError
from app.tools.llm_format import registry_to_openai_tools

if TYPE_CHECKING:
    from app.brain.conversation_manager import ConversationManager
    from app.brain.model_router import ModelRouter
    from app.config.settings import Settings
    from app.services.tool_loop import ToolLoopService
    from app.tools.registry.registry import ToolRegistry


logger = logging.getLogger(LOGGER_CHAT)


class ChatService(BaseService):
    """Orchestrates multi-turn chat through the LLM provider layer.

    Persists user and assistant messages in a conversation session so
    Jarvis remembers context across turns. When tools are enabled, runs
    an agentic tool loop before returning the final assistant reply.

    Attributes:
        _model_router: Model selection and provider resolution.
        _conversation_manager: Conversation session tracking.
        _tool_registry: Registered tools for function calling.
        _tool_loop: Tool execution loop service.
    """

    def __init__(
        self,
        settings: Settings,
        model_router: ModelRouter,
        conversation_manager: ConversationManager,
        tool_registry: ToolRegistry,
        tool_loop: ToolLoopService,
    ) -> None:
        """Initialize the chat service.

        Args:
            settings: Application configuration.
            model_router: Model router with registered provider adapters.
            conversation_manager: Conversation lifecycle manager.
            tool_registry: Tool registry for function definitions.
            tool_loop: Tool-calling loop executor.
        """
        super().__init__(settings)
        self._model_router = model_router
        self._conversation_manager = conversation_manager
        self._tool_registry = tool_registry
        self._tool_loop = tool_loop

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

        use_tools = (
            request.enable_tools
            and self._settings.tools_enabled
            and self._tool_registry.count() > 0
        )
        tools = registry_to_openai_tools(self._tool_registry) if use_tools else []

        logger.info(
            "Chat request | conversation=%s provider=%s model=%s turns=%d tools=%d",
            conversation.id,
            provider_name.value,
            model_id,
            len(messages),
            len(tools),
        )

        tool_summaries: list[ToolInvocationSummary] = []
        try:
            if use_tools:
                llm_response, tool_summaries = (
                    await self._tool_loop.complete_with_tools(
                        provider,
                        model_info,
                        messages,
                        tools,
                        temperature=request.temperature,
                        max_tokens=request.max_tokens,
                        confirmed=request.confirm,
                    )
                )
            else:
                llm_request = LLMRequest(
                    model=model_info,
                    messages=messages,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                )
                llm_response = await provider.complete(llm_request)
        except ToolConfirmationRequiredError as exc:
            return ChatResponse(
                message=(
                    "This action requires confirmation. "
                    "Resend your message with confirm=true to proceed."
                ),
                conversation_id=conversation.id,
                model=model_id,
                provider=provider_name.value,
                confirmation_required=True,
                pending_tool_id=exc.tool_id,
            )

        await self._conversation_manager.add_assistant_message(
            conversation.id,
            llm_response.content,
        )

        logger.info(
            "Chat response | conversation=%s model=%s finish_reason=%s tools=%d",
            conversation.id,
            llm_response.model.model_id,
            llm_response.finish_reason,
            len(tool_summaries),
        )

        return ChatResponse(
            message=llm_response.content,
            conversation_id=conversation.id,
            model=llm_response.model.model_id,
            provider=provider_name.value,
            finish_reason=llm_response.finish_reason,
            usage=llm_response.usage,
            tools_used=tool_summaries,
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
