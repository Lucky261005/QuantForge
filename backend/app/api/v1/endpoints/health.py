import redis
from fastapi import APIRouter, Response
from sqlalchemy import text

from app.api.deps import DbSession
from app.core.config import settings
from app.schemas.common import Message, ReadinessCheck, ReadinessResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=Message)
def health_check() -> Message:
    """Liveness probe — process is up and able to handle a request. Deliberately
    checks nothing else; see /health/ready for dependency checks."""
    return Message(message="ok")


@router.get("/health/ready", response_model=ReadinessResponse)
def readiness_check(response: Response, db: DbSession) -> ReadinessResponse:
    """Readiness probe — checks the dependencies a request actually needs. The
    database is a hard dependency (fails readiness if unreachable); Redis is a soft
    dependency, since the app has a documented graceful fallback for both the
    market-data cache (in-memory) and Celery (synchronous execution) — so a Redis
    outage is reported as degraded rather than making the whole app "not ready"."""
    checks: dict[str, ReadinessCheck] = {}

    try:
        db.execute(text("SELECT 1"))
        checks["database"] = ReadinessCheck(status="ok")
    except Exception as exc:  # noqa: BLE001 — report any failure as a readiness check result, not a 500
        checks["database"] = ReadinessCheck(status="error", detail=str(exc))

    try:
        redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=1.5).ping()
        checks["redis"] = ReadinessCheck(status="ok")
    except Exception as exc:  # noqa: BLE001
        checks["redis"] = ReadinessCheck(status="degraded", detail=str(exc))

    is_ready = checks["database"].status == "ok"
    response.status_code = 200 if is_ready else 503
    return ReadinessResponse(ready=is_ready, checks=checks)
