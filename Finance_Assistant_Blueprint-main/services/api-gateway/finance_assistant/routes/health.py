"""Meridian API — Health Check Routes.

Provides /health and /ready endpoints for container orchestrators
(ECS, ALB target group health checks).
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Liveness probe — confirms the process is running.

    Used by ECS task health check and ALB target group health check.
    Should always return 200 unless the process is deadlocked.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "service": "meridian-api",
    }


@router.get("/ready")
async def readiness_check() -> dict[str, object]:
    """Readiness probe — confirms the service can handle traffic.

    Checks critical dependencies (database, cache) are reachable.
    Returns 503 if any dependency is down.

    TODO: Add actual database and Redis connectivity checks
    once those connections are established (Phase 2).
    """
    checks: dict[str, str] = {
        "database": "ok",  # TODO: check asyncpg connection
        "cache": "ok",  # TODO: check Redis connection
    }

    all_healthy = all(v == "ok" for v in checks.values())

    return {
        "status": "ready" if all_healthy else "degraded",
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "checks": checks,
    }
