"""Health check API routes."""

from __future__ import annotations

from fastapi import APIRouter

from app.dependencies import HealthServiceDep
from app.models.health import HealthResponse, RootResponse, VersionResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/",
    response_model=RootResponse,
    summary="Root endpoint",
    description="Returns application metadata and documentation link.",
)
def root(health_service: HealthServiceDep) -> RootResponse:
    """Return welcome payload with application metadata."""
    return health_service.get_root()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns service health status for load balancers and monitors.",
)
def health(health_service: HealthServiceDep) -> HealthResponse:
    """Return application health status."""
    return health_service.get_health()


@router.get(
    "/version",
    response_model=VersionResponse,
    summary="Version information",
    description="Returns application name, version, and environment.",
)
def version(health_service: HealthServiceDep) -> VersionResponse:
    """Return application version information."""
    return health_service.get_version()
