"""Execution context preparation and merging."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.brain.schemas.context import ExecutionContext
from app.brain.schemas.conversation import Conversation
from app.brain.schemas.prompt import Prompt, PromptType

if TYPE_CHECKING:
    from app.brain.interfaces.context_provider import ContextProvider
    from app.brain.prompt_manager import PromptManager


class ContextManager:
    """Prepares merged execution context for planning and LLM requests.

    Combines conversation history, prompts, session data, environment
    metadata, and a placeholder for future long-term memory.

    Attributes:
        _context_provider: Context data port.
        _prompt_manager: Prompt resolution component.
    """

    def __init__(
        self,
        context_provider: ContextProvider,
        prompt_manager: PromptManager,
    ) -> None:
        """Initialize with context and prompt dependencies.

        Args:
            context_provider: Source for session/environment/memory context.
            prompt_manager: Prompt resolution component.
        """
        self._context_provider = context_provider
        self._prompt_manager = prompt_manager

    async def prepare(
        self,
        conversation: Conversation | None,
        *,
        session_id: str | None = None,
        memory_query: str | None = None,
    ) -> ExecutionContext:
        """Build a complete execution context.

        Args:
            conversation: Active conversation, if any.
            session_id: Optional session identifier.
            memory_query: Optional query for future memory retrieval.

        Returns:
            Merged ``ExecutionContext`` ready for the Planner or LLM layer.
        """
        base = await self._context_provider.build_context(
            conversation=conversation,
            session_id=session_id,
        )
        memory = await self._context_provider.get_memory_context(
            query=memory_query or "",
            conversation=conversation,
        )
        prompts = await self._prompt_manager.get_active_prompts()

        return ExecutionContext(
            conversation=base.conversation,
            system_prompts=prompts,
            session=base.session,
            environment=base.environment,
            memory=memory,
            metadata=base.metadata,
        )

    async def enrich(
        self,
        context: ExecutionContext,
        extra: dict[str, Any],
    ) -> ExecutionContext:
        """Return a copy of context with additional metadata merged.

        Args:
            context: Existing execution context.
            extra: Metadata to merge.

        Returns:
            New context with merged metadata.
        """
        merged = {**context.metadata, **extra}
        return context.model_copy(update={"metadata": merged})

    async def attach_prompts(
        self,
        context: ExecutionContext,
        prompt_types: list[PromptType],
    ) -> ExecutionContext:
        """Attach prompts of specific types to an existing context.

        Args:
            context: Existing execution context.
            prompt_types: Prompt types to include.

        Returns:
            Context with additional prompts appended.
        """
        prompts: list[Prompt] = list(context.system_prompts)
        for prompt_type in prompt_types:
            prompts.extend(await self._prompt_manager.get_prompts_by_type(prompt_type))
        return context.model_copy(update={"system_prompts": prompts})
