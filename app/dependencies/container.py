"""Dependency injection container for application services."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.brain.factory import BrainContainer, build_brain
from app.services.chat import ChatService
from app.services.conversation import ConversationService
from app.services.health import HealthService
from app.tools.factory import ToolPlatformContainer, build_tool_platform

if TYPE_CHECKING:
    from app.config.settings import Settings


@dataclass
class ServiceContainer:
    """Holds application service instances for dependency injection.

    Attributes:
        settings: Application configuration.
        health_service: Health and status reporting service.
        chat_service: Chat completion service.
        conversation_service: Conversation session service.
        brain: AI Core subsystem container (Sprint 2+).
        tools: Tool platform container (Sprint 3+).
    """

    settings: Settings
    health_service: HealthService
    chat_service: ChatService
    conversation_service: ConversationService
    brain: BrainContainer
    tools: ToolPlatformContainer


def build_container(settings: Settings) -> ServiceContainer:
    """Construct the service container with all registered services.

    Args:
        settings: Application settings.

    Returns:
        Populated service container.
    """
    brain = build_brain(settings)
    return ServiceContainer(
        settings=settings,
        health_service=HealthService(settings),
        chat_service=ChatService(
            settings,
            brain.model_router,
            brain.conversation_manager,
        ),
        conversation_service=ConversationService(brain.conversation_manager),
        brain=brain,
        tools=build_tool_platform(),
    )
