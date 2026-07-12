"""Meridian API — FastAPI Application Factory.

Entry point for the Meridian API service.
Uses the application factory pattern for testability.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .cache import close_redis, init_redis
from .config import Settings, get_settings
from .database import close_database, init_database
from .exceptions import register_exception_handlers
from .logging import get_logger, setup_logging
from .middleware import RequestIdMiddleware, RequestLoggingMiddleware
from .routes.chat import router as chat_router
from .routes.documents import router as documents_router
from .routes.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan — startup and shutdown logic.

    Initializes and cleans up:
    - Database connection pool (asyncpg via SQLAlchemy)
    - Redis connection
    - Background tasks (future)
    """
    logger = get_logger(__name__)
    settings = get_settings()

    await logger.ainfo(
        "Starting Meridian API",
        environment=settings.environment,
        log_level=settings.log_level,
    )

    # === Startup ===
    await init_database(settings)
    await init_redis(settings)
    # TODO: Initialize Bedrock client (Phase 3)

    yield  # Application runs here

    # === Shutdown ===
    await logger.ainfo("Shutting down Meridian API")
    await close_redis()
    await close_database()


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
    app.include_router(chat_router)
    app.include_router(documents_router)

    return app


# Default app instance for uvicorn
app = create_app()
