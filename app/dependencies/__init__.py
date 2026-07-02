"""FastAPI dependency injection providers."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from starlette.requests import HTTPConnection

from app.config.settings import Settings
from app.dependencies.container import ServiceContainer
from app.services.chat import ChatService
from app.services.conversation import ConversationService
from app.services.health import HealthService
from app.services.memory import MemoryService
from app.services.voice import VoiceService
from app.services.voice_platform import VoicePlatformService


def get_app_settings(conn: HTTPConnection) -> Settings:
    """Return settings bound to the running application instance.

    Reads from ``app.state`` so test overrides and per-app configuration
    are respected instead of the global ``get_settings()`` cache.

    Args:
        conn: Current HTTP or WebSocket connection.

    Returns:
        Application settings for the active app instance.
    """
    settings: Settings = conn.app.state.settings
    return settings


def get_service_container(conn: HTTPConnection) -> ServiceContainer:
    """Return the application service container from connection state.

    Args:
        conn: Current HTTP or WebSocket connection.

    Returns:
        Service container with registered services.
    """
    container: ServiceContainer = conn.app.state.container
    return container


def get_health_service(
    container: Annotated[ServiceContainer, Depends(get_service_container)],
) -> HealthService:
    """Provide the health service from the container.

    Args:
        container: Application service container.

    Returns:
        Health service instance.
    """
    return container.health_service


def get_chat_service(
    container: Annotated[ServiceContainer, Depends(get_service_container)],
) -> ChatService:
    """Provide the chat service from the container.

    Args:
        container: Application service container.

    Returns:
        Chat service instance.
    """
    return container.chat_service


def get_conversation_service(
    container: Annotated[ServiceContainer, Depends(get_service_container)],
) -> ConversationService:
    """Provide the conversation service from the container.

    Args:
        container: Application service container.

    Returns:
        Conversation service instance.
    """
    return container.conversation_service


def get_memory_service(
    container: Annotated[ServiceContainer, Depends(get_service_container)],
) -> MemoryService:
    """Provide the memory service from the container.

    Args:
        container: Application service container.

    Returns:
        Memory service instance.
    """
    return container.memory_service


def get_voice_service(
    container: Annotated[ServiceContainer, Depends(get_service_container)],
) -> VoiceService:
    """Provide the voice service from the container.

    Args:
        container: Application service container.

    Returns:
        Voice service instance.
    """
    return container.voice_service


def get_voice_platform_service(
    container: Annotated[ServiceContainer, Depends(get_service_container)],
) -> VoicePlatformService:
    """Provide the voice platform service from the container."""
    return container.voice_platform_service


SettingsDep = Annotated[Settings, Depends(get_app_settings)]
HealthServiceDep = Annotated[HealthService, Depends(get_health_service)]
ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
ConversationServiceDep = Annotated[
    ConversationService,
    Depends(get_conversation_service),
]
MemoryServiceDep = Annotated[MemoryService, Depends(get_memory_service)]
VoiceServiceDep = Annotated[VoiceService, Depends(get_voice_service)]
VoicePlatformServiceDep = Annotated[
    VoicePlatformService,
    Depends(get_voice_platform_service),
]
ContainerDep = Annotated[ServiceContainer, Depends(get_service_container)]
