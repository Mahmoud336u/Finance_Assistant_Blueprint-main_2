"""Meridian API — Health Check Routes.

Provides /health and /ready endpoints for container orchestrators
(ECS, ALB target group health checks).
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter
from starlette.responses import JSONResponse

from ..cache import check_redis_health
from ..database import check_database_health

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
async def readiness_check() -> JSONResponse:
    """Readiness probe — confirms the service can handle traffic.

    Checks critical dependencies (database, cache) are reachable.
    Returns 503 if any dependency is down.
    """
    db_ok = await check_database_health()
    redis_ok = await check_redis_health()

    checks: dict[str, str] = {
        "database": "ok" if db_ok else "unavailable",
        "cache": "ok" if redis_ok else "unavailable",
    }

    all_healthy = all(v == "ok" for v in checks.values())
    status_code = 200 if all_healthy else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if all_healthy else "degraded",
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "checks": checks,
        },
    )

