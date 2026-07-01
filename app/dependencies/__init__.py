"""FastAPI dependency injection providers."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.config.settings import Settings
from app.dependencies.container import ServiceContainer
from app.services.chat import ChatService
from app.services.health import HealthService


def get_app_settings(request: Request) -> Settings:
    """Return settings bound to the running application instance.

    Reads from ``app.state`` so test overrides and per-app configuration
    are respected instead of the global ``get_settings()`` cache.

    Args:
        request: Current HTTP request.

    Returns:
        Application settings for the active app instance.
    """
    settings: Settings = request.app.state.settings
    return settings


def get_service_container(request: Request) -> ServiceContainer:
    """Return the application service container from request state.

    Args:
        request: Current HTTP request.

    Returns:
        Service container with registered services.
    """
    container: ServiceContainer = request.app.state.container
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


SettingsDep = Annotated[Settings, Depends(get_app_settings)]
HealthServiceDep = Annotated[HealthService, Depends(get_health_service)]
ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
ContainerDep = Annotated[ServiceContainer, Depends(get_service_container)]
