"""Dependency injection container for application services."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.brain.factory import BrainContainer, build_brain
from app.memory.factory import build_memory_store
from app.services.chat import ChatService
from app.services.conversation import ConversationService
from app.services.health import HealthService
from app.services.memory import MemoryService
from app.services.tool_loop import ToolLoopService
from app.services.voice import VoiceService
from app.services.voice_platform import VoicePlatformService
from app.tools.factory import ToolPlatformContainer, build_tool_platform
from app.voice.factory import VoicePlatformContainer, build_voice_platform

if TYPE_CHECKING:
    from app.config.settings import Settings
    from app.memory.interfaces.memory_store import MemoryStore


@dataclass
class ServiceContainer:
    """Holds application service instances for dependency injection.

    Attributes:
        settings: Application configuration.
        health_service: Health and status reporting service.
        chat_service: Chat completion service.
        conversation_service: Conversation session service.
        memory_service: Long-term memory service.
        voice_service: WebSocket voice turn service.
        voice_platform_service: Local voice platform lifecycle service.
        voice_platform: Voice platform component container.
        brain: AI Core subsystem container (Sprint 2+).
        tools: Tool platform container (Sprint 3+).
        memory_store: Long-term memory persistence adapter.
    """

    settings: Settings
    health_service: HealthService
    chat_service: ChatService
    conversation_service: ConversationService
    memory_service: MemoryService
    voice_service: VoiceService
    voice_platform_service: VoicePlatformService
    voice_platform: VoicePlatformContainer
    brain: BrainContainer
    tools: ToolPlatformContainer
    memory_store: MemoryStore


def build_container(settings: Settings) -> ServiceContainer:
    """Construct the service container with all registered services.

    Args:
        settings: Application settings.

    Returns:
        Populated service container.
    """
    brain = build_brain(settings)
    tools = build_tool_platform(settings=settings)
    memory_store = build_memory_store(settings)
    memory_service = MemoryService(memory_store, settings)
    tool_loop = ToolLoopService(
        tools.registry,
        tools.executor,
        max_iterations=settings.chat_max_tool_iterations,
    )
    chat_service = ChatService(
        settings,
        brain.model_router,
        brain.conversation_manager,
        tools.registry,
        tool_loop,
        memory_service,
    )
    voice_platform = build_voice_platform(settings, chat_service)
    voice_service = VoiceService(
        settings,
        chat_service,
        voice_platform.stt,
        voice_platform.tts,
        conversation=voice_platform.conversation,
    )
    voice_platform_service = VoicePlatformService(settings, voice_platform)
    return ServiceContainer(
        settings=settings,
        health_service=HealthService(settings),
        chat_service=chat_service,
        conversation_service=ConversationService(brain.conversation_manager),
        memory_service=memory_service,
        voice_service=voice_service,
        voice_platform_service=voice_platform_service,
        voice_platform=voice_platform,
        brain=brain,
        tools=tools,
        memory_store=memory_store,
    )
