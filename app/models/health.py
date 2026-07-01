"""Health endpoint response models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RootResponse(BaseModel):
    """Response model for the root endpoint."""

    name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Current deployment environment")
    docs: str = Field(..., description="OpenAPI documentation path")


class HealthResponse(BaseModel):
    """Response model for the health check endpoint."""

    status: str = Field(..., description="Health status indicator")
    environment: str = Field(..., description="Current deployment environment")
    timestamp: str = Field(..., description="UTC timestamp of the health check")


class VersionResponse(BaseModel):
    """Response model for the version endpoint."""

    name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Current deployment environment")
