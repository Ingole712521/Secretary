"""Dependency injection container for application services."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.brain.factory import BrainContainer, build_brain
from app.services.health import HealthService

if TYPE_CHECKING:
    from app.config.settings import Settings


@dataclass
class ServiceContainer:
    """Holds application service instances for dependency injection.

    Attributes:
        settings: Application configuration.
        health_service: Health and status reporting service.
        brain: AI Core subsystem container (Sprint 2+).
    """

    settings: Settings
    health_service: HealthService
    brain: BrainContainer


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
        brain=build_brain(settings),
    )
