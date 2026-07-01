"""Jarvis OS Brain — AI Core architecture package.

The Brain coordinates conversation tracking, context preparation,
prompt management, model routing, and plan generation. It does not
execute tasks or call external LLM APIs in Sprint 2.
"""

from app.brain.context_manager import ContextManager
from app.brain.conversation_manager import ConversationManager
from app.brain.exceptions import (
    BrainError,
    ConversationNotFoundError,
    ModelRoutingError,
    PlanGenerationError,
    PromptNotFoundError,
)
from app.brain.factory import BrainContainer, build_brain
from app.brain.model_router import ModelRouter
from app.brain.orchestrator import Orchestrator
from app.brain.planner import BrainPlanner
from app.brain.prompt_manager import PromptManager

__all__ = [
    "BrainContainer",
    "BrainError",
    "BrainPlanner",
    "ConversationManager",
    "ConversationNotFoundError",
    "ContextManager",
    "ModelRouter",
    "ModelRoutingError",
    "Orchestrator",
    "PlanGenerationError",
    "PromptManager",
    "PromptNotFoundError",
    "build_brain",
]
