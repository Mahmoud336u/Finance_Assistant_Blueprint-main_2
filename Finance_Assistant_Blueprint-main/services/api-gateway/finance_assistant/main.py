"""Meridian API — FastAPI Application Factory.

Entry point for the Meridian API service.
Uses the application factory pattern for testability.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings, get_settings
from .exceptions import register_exception_handlers
from .logging import get_logger, setup_logging
from .middleware import RequestIdMiddleware, RequestLoggingMiddleware
from .routes.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan — startup and shutdown logic.

    Use this for initializing and cleaning up resources:
    - Database connection pools
    - Redis connections
    - Background tasks

    TODO (Phase 2): Initialize database and cache connections here.
    """
    logger = get_logger(__name__)
    settings = get_settings()

    await logger.ainfo(
        "Starting Meridian API",
        environment=settings.environment,
        log_level=settings.log_level,
    )

    # === Startup ===
    # TODO: Initialize database pool (Phase 2)
    # TODO: Initialize Redis connection (Phase 2)
    # TODO: Initialize Bedrock client (Phase 3)

    yield  # Application runs here

    # === Shutdown ===
    await logger.ainfo("Shutting down Meridian API")
    # TODO: Close database pool (Phase 2)
    # TODO: Close Redis connection (Phase 2)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        settings: Optional settings override (useful for testing).

    Returns:
        Configured FastAPI application instance.
    """
    if settings is None:
        settings = get_settings()

    # Configure structured logging
    setup_logging(
        log_level=settings.log_level,
        json_output=settings.is_production,
    )

    app = FastAPI(
        title="Meridian API",
        description="Enterprise Multi-Region RAG Platform for Financial Intelligence",
        version="0.1.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # --- Middleware (order matters: first added = outermost) ---
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Response-Time-Ms"],
    )

    # --- Exception handlers ---
    register_exception_handlers(app)

    # --- Routes ---
    app.include_router(health_router)
    # TODO: app.include_router(v1_router, prefix="/v1")

    return app


# Default app instance for uvicorn
app = create_app()
