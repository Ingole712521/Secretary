"""FastAPI dependency injection providers."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.config.settings import Settings, get_settings
from app.dependencies.container import ServiceContainer
from app.services.health import HealthService


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


SettingsDep = Annotated[Settings, Depends(get_settings)]
HealthServiceDep = Annotated[HealthService, Depends(get_health_service)]
ContainerDep = Annotated[ServiceContainer, Depends(get_service_container)]
