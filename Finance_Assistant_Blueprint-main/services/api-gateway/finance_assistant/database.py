"""Meridian — Async Database Connection Manager.

Provides an async SQLAlchemy engine and session factory
using asyncpg for PostgreSQL connections.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .config import Settings, get_settings
from .logging import get_logger

logger = get_logger(__name__)

# Module-level engine and session factory (initialized on app startup)
_engine = None
_session_factory = None


async def init_database(settings: Settings | None = None) -> None:
    """Initialize the async database engine and session factory.

    Called during application lifespan startup. Creates an asyncpg
    connection pool with the configured pool size.

    Args:
        settings: Application settings (defaults to singleton).
    """
    global _engine, _session_factory

    if settings is None:
        settings = get_settings()

    _engine = create_async_engine(
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        echo=settings.database_echo,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    await logger.ainfo(
        "Database engine initialized",
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
    )


async def close_database() -> None:
    """Dispose of the database engine and close all connections.

    Called during application lifespan shutdown.
    """
    global _engine, _session_factory

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        await logger.ainfo("Database engine closed")


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session.

    Use as a FastAPI dependency::

        @router.get("/users")
        async def list_users(db: AsyncSession = Depends(get_db_session)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    if _session_factory is None:
        msg = "Database not initialized. Call init_database() first."
        raise RuntimeError(msg)

    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_database_health() -> bool:
    """Check if the database is reachable.

    Returns:
        True if a simple query succeeds, False otherwise.
    """
    if _engine is None:
        return False

    try:
        async with _engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        await logger.awarning("Database health check failed", error=str(exc))
        return False


# Import here to avoid circular imports
from sqlalchemy import text  # noqa: E402
