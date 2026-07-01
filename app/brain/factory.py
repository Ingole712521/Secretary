"""Brain subsystem factory and dependency wiring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.brain.context_manager import ContextManager
from app.brain.conversation_manager import ConversationManager
from app.brain.model_router import ModelRouter
from app.brain.orchestrator import Orchestrator
from app.brain.planner import BrainPlanner
from app.brain.prompt_manager import PromptManager
from app.brain.stores.context_provider import StubContextProvider
from app.brain.stores.conversation_store import InMemoryConversationStore
from app.brain.stores.prompt_provider import InMemoryPromptProvider

if TYPE_CHECKING:
    from app.config.settings import Settings


@dataclass
class BrainContainer:
    """Holds all Brain subsystem components for dependency injection.

    Attributes:
        orchestrator: Central Brain coordinator.
        conversation_manager: Conversation lifecycle manager.
        context_manager: Execution context assembler.
        prompt_manager: Prompt template manager.
        model_router: Model selection registry.
        planner: Plan generation component.
    """

    orchestrator: Orchestrator
    conversation_manager: ConversationManager
    context_manager: ContextManager
    prompt_manager: PromptManager
    model_router: ModelRouter
    planner: BrainPlanner


def build_brain(settings: Settings) -> BrainContainer:
    """Construct the Brain subsystem with in-memory Sprint 2 adapters.

    Args:
        settings: Application settings for environment context.

    Returns:
        Fully wired ``BrainContainer``.
    """
    conversation_store = InMemoryConversationStore()
    prompt_provider = InMemoryPromptProvider()
    context_provider = StubContextProvider(
        app_env=settings.app_env.value,
        app_version=settings.app_version,
    )

    conversation_manager = ConversationManager(conversation_store)
    prompt_manager = PromptManager(prompt_provider)
    context_manager = ContextManager(context_provider, prompt_manager)
    model_router = ModelRouter()
    planner = BrainPlanner()

    orchestrator = Orchestrator(
        conversation_manager=conversation_manager,
        context_manager=context_manager,
        prompt_manager=prompt_manager,
        model_router=model_router,
        planner=planner,
    )

    return BrainContainer(
        orchestrator=orchestrator,
        conversation_manager=conversation_manager,
        context_manager=context_manager,
        prompt_manager=prompt_manager,
        model_router=model_router,
        planner=planner,
    )
