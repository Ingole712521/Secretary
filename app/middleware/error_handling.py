"""Global exception handlers and error response formatting."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.exceptions import (
    AuthenticationException,
    ConfigurationException,
    JarvisError,
    ToolException,
    ValidationException,
)
from app.models.common import ErrorDetail, ErrorResponse

if TYPE_CHECKING:
    from app.config.settings import Settings

logger = logging.getLogger("jarvis.errors")

_STATUS_MAP: dict[type[JarvisError], int] = {
    ValidationException: 422,
    ConfigurationException: 500,
    ToolException: 500,
    AuthenticationException: 401,
    JarvisError: 500,
}


def _correlation_id(request: Request) -> str | None:
    """Extract correlation ID from request state."""
    return getattr(request.state, "correlation_id", None)


def _error_response(
    *,
    request: Request,
    code: str,
    message: str,
    status_code: int,
) -> JSONResponse:
    """Build a standardized JSON error response.

    Args:
        request: Current HTTP request.
        code: Machine-readable error code.
        message: Human-readable error message.
        status_code: HTTP status code.

    Returns:
        JSON response with error envelope.
    """
    body = ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message,
            correlation_id=_correlation_id(request),
        )
    )
    return JSONResponse(status_code=status_code, content=body.model_dump())


def register_exception_handlers(app: FastAPI, _settings: Settings) -> None:
    """Register exception handlers on the FastAPI application.

    Args:
        app: FastAPI application.
        _settings: Application settings (reserved for future use).
    """

    @app.exception_handler(JarvisError)
    async def jarvis_error_handler(
        request: Request,
        exc: JarvisError,
    ) -> JSONResponse:
        """Handle application-specific exceptions."""
        status_code = _STATUS_MAP.get(type(exc), 500)
        logger.error(
            "application error: %s",
            exc.message,
            extra={"correlation_id": _correlation_id(request), "code": exc.code},
        )
        return _error_response(
            request=request,
            code=exc.code,
            message=exc.message,
            status_code=status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Handle FastAPI/Pydantic request validation errors."""
        message = "Request validation failed"
        logger.warning(
            message,
            extra={"correlation_id": _correlation_id(request), "errors": exc.errors()},
        )
        return _error_response(
            request=request,
            code="VALIDATION_ERROR",
            message=message,
            status_code=422,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        """Handle Starlette HTTP exceptions."""
        return _error_response(
            request=request,
            code="HTTP_ERROR",
            message=str(exc.detail),
            status_code=exc.status_code,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Handle unexpected exceptions."""
        logger.exception(
            "unhandled exception",
            extra={"correlation_id": _correlation_id(request)},
        )
        return _error_response(
            request=request,
            code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            status_code=500,
        )
