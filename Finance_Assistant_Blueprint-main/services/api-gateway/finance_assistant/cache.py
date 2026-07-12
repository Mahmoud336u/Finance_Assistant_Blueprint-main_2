"""Meridian — Redis Connection Manager.

Provides an async Redis client for caching, session storage,
and real-time budget state per the blueprint's architecture.
"""

from __future__ import annotations

from typing import Any

import redis.asyncio as aioredis

from .config import Settings, get_settings
from .logging import get_logger

logger = get_logger(__name__)

# Module-level Redis client (initialized on app startup)
_redis_client: aioredis.Redis | None = None


async def init_redis(settings: Settings | None = None) -> None:
    """Initialize the async Redis connection.

    Called during application lifespan startup.

    Args:
        settings: Application settings (defaults to singleton).
    """
    global _redis_client

    if settings is None:
        settings = get_settings()

    _redis_client = aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
        max_connections=20,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
    )

    await logger.ainfo("Redis client initialized", url=settings.redis_url.split("@")[-1])


async def close_redis() -> None:
    """Close the Redis connection.

    Called during application lifespan shutdown.
    """
    global _redis_client

    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
        await logger.ainfo("Redis client closed")


def get_redis() -> aioredis.Redis:
    """Get the Redis client instance.

    Use as a FastAPI dependency or direct import::

        @router.get("/cached-data")
        async def get_data(cache: Redis = Depends(get_redis)):
            cached = await cache.get("key")
            ...

    Raises:
        RuntimeError: If Redis has not been initialized.
    """
    if _redis_client is None:
        msg = "Redis not initialized. Call init_redis() first."
        raise RuntimeError(msg)
    return _redis_client


async def check_redis_health() -> bool:
    """Check if Redis is reachable.

    Returns:
        True if PING succeeds, False otherwise.
    """
    if _redis_client is None:
        return False

    try:
        pong = await _redis_client.ping()
        return bool(pong)
    except Exception as exc:
        await logger.awarning("Redis health check failed", error=str(exc))
        return False


# ============================================================
# Cache Utilities
# ============================================================


async def cache_get(key: str) -> str | None:
    """Get a value from cache.

    Args:
        key: Cache key.

    Returns:
        Cached value or None if not found / Redis unavailable.
    """
    try:
        client = get_redis()
        return await client.get(key)
    except (RuntimeError, aioredis.RedisError) as exc:
        await logger.awarning("Cache get failed", key=key, error=str(exc))
        return None


async def cache_set(key: str, value: str, ttl: int | None = None) -> bool:
    """Set a value in cache.

    Args:
        key: Cache key.
        value: Value to store.
        ttl: Time-to-live in seconds (None = use default from settings).

    Returns:
        True if successful, False otherwise.
    """
    try:
        client = get_redis()
        if ttl is None:
            ttl = get_settings().redis_cache_ttl_seconds
        await client.set(key, value, ex=ttl)
        return True
    except (RuntimeError, aioredis.RedisError) as exc:
        await logger.awarning("Cache set failed", key=key, error=str(exc))
        return False


async def cache_delete(key: str) -> bool:
    """Delete a key from cache.

    Args:
        key: Cache key.

    Returns:
        True if successful, False otherwise.
    """
    try:
        client = get_redis()
        await client.delete(key)
        return True
    except (RuntimeError, aioredis.RedisError) as exc:
        await logger.awarning("Cache delete failed", key=key, error=str(exc))
        return False


async def cache_json_get(key: str) -> dict[str, Any] | None:
    """Get a JSON value from cache (deserialized).

    Args:
        key: Cache key.

    Returns:
        Deserialized dict or None.
    """
    import json

    raw = await cache_get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


async def cache_json_set(key: str, value: dict[str, Any], ttl: int | None = None) -> bool:
    """Set a JSON value in cache (serialized).

    Args:
        key: Cache key.
        value: Dict to serialize and store.
        ttl: Time-to-live in seconds.

    Returns:
        True if successful.
    """
    import json

    return await cache_set(key, json.dumps(value, default=str), ttl=ttl)
