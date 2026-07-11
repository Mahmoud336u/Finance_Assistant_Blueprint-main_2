"""Meridian API — Exception Hierarchy and Error Handling.

Provides structured error responses and a global exception handler
for the FastAPI application.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .logging import get_logger

logger = get_logger(__name__)


# ============================================================
# Exception Hierarchy
# ============================================================


class MeridianError(Exception):
    """Base exception for all Meridian application errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class NotFoundError(MeridianError):
    """Resource not found."""

    def __init__(self, resource: str, resource_id: str) -> None:
        super().__init__(
            message=f"{resource} not found: {resource_id}",
            code="NOT_FOUND",
            status_code=404,
            details={"resource": resource, "id": resource_id},
        )


class ValidationError(MeridianError):
    """Request validation failed."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )


class AuthenticationError(MeridianError):
    """Authentication failed."""

    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401,
        )


class AuthorizationError(MeridianError):
    """Authorization failed."""

    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=403,
        )


class RateLimitError(MeridianError):
    """Rate limit exceeded."""

    def __init__(self, retry_after: int = 60) -> None:
        super().__init__(
            message="Rate limit exceeded. Please retry later.",
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={"retry_after_seconds": retry_after},
        )


class ExternalServiceError(MeridianError):
    """External service call failed (Bedrock, Plaid, etc.)."""

    def __init__(self, service: str, message: str) -> None:
        super().__init__(
            message=f"External service error ({service}): {message}",
            code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details={"service": service},
        )


# ============================================================
# Error Response Schema
# ============================================================


def _error_response(
    request_id: str,
    code: str,
    message: str,
    status_code: int,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a standardized error response body."""
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
        "meta": {
            "request_id": request_id,
        },
    }


# ============================================================
# Exception Handlers
# ============================================================


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI app."""

    @app.exception_handler(MeridianError)
    async def meridian_error_handler(request: Request, exc: MeridianError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "unknown")
        logger.warning(
            "Application error",
            code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
            request_id=request_id,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_response(
                request_id=request_id,
                code=exc.code,
                message=exc.message,
                status_code=exc.status_code,
                details=exc.details,
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "unknown")
        logger.exception(
            "Unhandled exception",
            request_id=request_id,
            error=str(exc),
        )
        return JSONResponse(
            status_code=500,
            content=_error_response(
                request_id=request_id,
                code="INTERNAL_ERROR",
                message="An unexpected error occurred. Please try again later.",
                status_code=500,
            ),
        )
