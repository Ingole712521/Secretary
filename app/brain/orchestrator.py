"""Brain orchestrator — coordinates all AI Core components."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.brain.schemas.conversation import Conversation
from app.brain.schemas.execution import (
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
)
from app.constants import LOGGER_ROOT

if TYPE_CHECKING:
    from app.brain.context_manager import ContextManager
    from app.brain.conversation_manager import ConversationManager
    from app.brain.interfaces.planner import Planner
    from app.brain.model_router import ModelRouter
    from app.brain.prompt_manager import PromptManager

logger = logging.getLogger(f"{LOGGER_ROOT}.brain.orchestrator")


class Orchestrator:
    """Central coordinator for the Jarvis OS Brain.

    Receives user requests and manages the execution lifecycle across
    conversation tracking, context preparation, prompt resolution, model
    routing, and plan generation.

    Sprint 2 orchestrates planning only. LLM inference and task execution
    are intentionally not implemented.

    Architecture flow::

        User Request
            → ConversationManager (track session)
            → ContextManager (merge context)
            → PromptManager (resolve prompts)
            → ModelRouter (select model metadata)
            → Planner (generate plan)
            → ExecutionResult

    Attributes:
        _conversation_manager: Conversation lifecycle manager.
        _context_manager: Execution context assembler.
        _prompt_manager: Prompt template manager.
        _model_router: Model selection and provider registry.
        _planner: Plan generation port implementation.
    """

    def __init__(
        self,
        conversation_manager: ConversationManager,
        context_manager: ContextManager,
        prompt_manager: PromptManager,
        model_router: ModelRouter,
        planner: Planner,
    ) -> None:
        """Initialize the orchestrator with injected dependencies.

        Args:
            conversation_manager: Conversation tracking component.
            context_manager: Context preparation component.
            prompt_manager: Prompt management component.
            model_router: Model routing component.
            planner: Plan generation implementation.
        """
        self._conversation_manager = conversation_manager
        self._context_manager = context_manager
        self._prompt_manager = prompt_manager
        self._model_router = model_router
        self._planner = planner

    async def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Process a user request through the Brain pipeline.

        Coordinates all Brain components and returns a planning result.
        Does not invoke LLM providers or execute plan tasks.

        Args:
            request: Structured user execution request.

        Returns:
            Execution result with optional plan and conversation ID.
        """
        logger.info(
            "brain execution started",
            extra={
                "require_plan": request.require_plan,
                "conversation_id": request.conversation_id,
            },
        )

        conversation = await self._track_conversation(request)
        context = await self._context_manager.prepare(
            conversation=conversation,
            session_id=request.session_id,
            memory_query=request.user_input,
        )

        # Model selection is metadata-only in Sprint 2.
        model = self._model_router.select_model()
        logger.debug(
            "model selected",
            extra={"provider": model.provider, "model_id": model.model_id},
        )

        # Prompt resolution is part of context; explicit access for clarity.
        _ = await self._prompt_manager.get_active_prompts()

        plan = None
        if request.require_plan:
            plan = await self._planner.create_plan(
                goal=request.user_input,
                context=context,
            )

        result = ExecutionResult(
            status=ExecutionStatus.PLANNED,
            plan=plan,
            conversation_id=conversation.id,
            message="Plan generated successfully" if plan else "Request processed",
            metadata={
                "model_provider": model.provider,
                "model_id": model.model_id,
            },
        )

        logger.info(
            "brain execution completed",
            extra={
                "conversation_id": conversation.id,
                "plan_id": plan.id if plan else None,
            },
        )
        return result

    async def _track_conversation(self, request: ExecutionRequest) -> Conversation:
        """Track or create the conversation for a request.

        Args:
            request: Incoming execution request.

        Returns:
            Active conversation instance.
        """
        conversation = await self._conversation_manager.get_or_create(
            request.conversation_id,
        )
        await self._conversation_manager.add_user_message(
            conversation.id,
            request.user_input,
        )
        refreshed = await self._conversation_manager.get_or_create(conversation.id)
        return refreshed
