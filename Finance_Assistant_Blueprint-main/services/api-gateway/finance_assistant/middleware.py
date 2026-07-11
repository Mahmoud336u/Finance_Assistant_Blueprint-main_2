"""Meridian API — Request Middleware.

Provides request ID injection, request logging, and timing middleware.
"""

from __future__ import annotations

import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Inject a unique request ID into every request.

    The request ID is:
    - Set from X-Request-ID header if provided (for distributed tracing)
    - Generated as a UUID4 if not provided
    - Added to response headers as X-Request-ID
    - Bound to structlog context for all log messages in the request
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        # Bind request context to structlog for this request
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log request start/end with timing information."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        logger = structlog.get_logger("request")

        start_time = time.perf_counter()

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Skip health check logging to reduce noise
        if request.url.path not in ("/health", "/ready", "/metrics"):
            await logger.ainfo(
                "request_completed",
                status_code=response.status_code,
                duration_ms=duration_ms,
                client_ip=request.client.host if request.client else "unknown",
            )

        response.headers["X-Response-Time-Ms"] = str(duration_ms)
        return response
