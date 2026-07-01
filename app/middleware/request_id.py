"""Request correlation ID middleware."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.constants import CORRELATION_ID_STATE_KEY

if TYPE_CHECKING:
    from app.config.settings import Settings


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Assign or propagate a correlation ID for each HTTP request."""

    def __init__(self, app: ASGIApp, *, settings: Settings) -> None:
        """Initialize middleware with settings.

        Args:
            app: ASGI application.
            settings: Application settings.
        """
        super().__init__(app)
        self._header_name = settings.correlation_id_header

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Attach a correlation ID to the request and response.

        Args:
            request: Incoming HTTP request.
            call_next: Next middleware or route handler.

        Returns:
            HTTP response with correlation ID header.
        """
        correlation_id = request.headers.get(self._header_name) or str(uuid.uuid4())
        setattr(request.state, CORRELATION_ID_STATE_KEY, correlation_id)

        response = await call_next(request)
        response.headers[self._header_name] = correlation_id
        return response
