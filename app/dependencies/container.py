"""Dependency injection container for application services."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from app.services.health import HealthService

if TYPE_CHECKING:
    from app.config.settings import Settings


class AIRouterServiceProtocol(Protocol):
    """Placeholder protocol for the future AI router service (Phase 2)."""

    async def route(self, intent: str) -> str:
        """Route an intent to the appropriate agent."""
        ...


class MemoryServiceProtocol(Protocol):
    """Placeholder protocol for the future memory service (Phase 3)."""

    async def retrieve(self, query: str) -> list[str]:
        """Retrieve relevant memories for a query."""
        ...


class ToolServiceProtocol(Protocol):
    """Placeholder protocol for the future tool framework (Phase 4)."""

    async def invoke(self, tool_name: str, params: dict[str, object]) -> object:
        """Invoke a registered tool."""
        ...


@dataclass
class ServiceContainer:
    """Holds application service instances for dependency injection.

    Attributes:
        settings: Application configuration.
        health_service: Health and status reporting service.
    """

    settings: Settings
    health_service: HealthService


def build_container(settings: Settings) -> ServiceContainer:
    """Construct the service container with all registered services.

    Args:
        settings: Application settings.

    Returns:
        Populated service container.
    """
    return ServiceContainer(
        settings=settings,
        health_service=HealthService(settings),
    )
