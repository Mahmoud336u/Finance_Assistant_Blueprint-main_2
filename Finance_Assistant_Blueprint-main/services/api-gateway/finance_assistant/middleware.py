"""Meridian API — Request Middleware.

Provides request ID injection, request logging, security headers,
and rate limiting middleware.
"""

from __future__ import annotations

import time
import uuid

import structlog
from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from .cache import get_redis

# Rate limiting configuration
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW_SECONDS = 60


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


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add OWASP-recommended security headers to all responses."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # Prevent browser MIME-sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Prevent framing (clickjacking)
        response.headers["X-Frame-Options"] = "DENY"
        # Enable XSS filtering
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # Enforce HTTPS
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Restrict permissions (e.g., camera, microphone)
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding window rate limiter backed by Redis.
    
    Limits requests per IP address or user ID to prevent abuse.
    Fails open (allows request) if Redis is unavailable.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip rate limiting for internal endpoints
        if request.url.path in ("/health", "/ready", "/metrics"):
            return await call_next(request)

        logger = structlog.get_logger(__name__)

        # Identify client (use IP if no auth header)
        client_ip = request.client.host if request.client else "unknown"
        # If user is authenticated, we'd ideally rate limit by user_id.
        # But middleware runs before route dependencies, so we use token hash or IP.
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # Hash the token to use as a key without storing the actual token
            import hashlib
            token = auth_header.split(" ")[1]
            identifier = f"user:{hashlib.sha256(token.encode()).hexdigest()[:16]}"
        else:
            identifier = f"ip:{client_ip}"

        key = f"ratelimit:{identifier}"

        try:
            redis = get_redis()
            
            # Sliding window using sorted sets
            now = time.time()
            window_start = now - RATE_LIMIT_WINDOW_SECONDS

            async with redis.pipeline(transaction=True) as pipe:
                # Remove old requests
                pipe.zremrangebyscore(key, 0, window_start)
                # Count requests in window
                pipe.zcard(key)
                # Add current request
                pipe.zadd(key, {str(now): now})
                # Update expiry to clean up
                pipe.expire(key, RATE_LIMIT_WINDOW_SECONDS)
                
                results = await pipe.execute()
                request_count = results[1]

            if request_count >= RATE_LIMIT_REQUESTS:
                await logger.awarning("Rate limit exceeded", identifier=identifier)
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Too Many Requests",
                        "message": "Rate limit exceeded. Please try again later.",
                    },
                    headers={"Retry-After": str(RATE_LIMIT_WINDOW_SECONDS)},
                )

        except Exception as exc:
            # Fail open if Redis is down
            await logger.aerror("Rate limiting failed, failing open", error=str(exc))

        return await call_next(request)
