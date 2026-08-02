from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi import HTTPException

from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.schemas.health import (
    HealthResponse,
    ReadinessCheck,
    ReadinessResponse,
)

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)

liveness_router = APIRouter(
    prefix="/health/live",
    tags=["Health"],
)

readiness_router = APIRouter(
    prefix="/health/ready",
    tags=["Health"],
)


@router.get(
    "",
    response_model=HealthResponse,
)
async def health_check():
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        service="SecureVault",
        version="1.0.0",
        environment=settings.APP_ENV,
    )


@liveness_router.get(
    "",
    response_model=HealthResponse,
)
async def liveness_check():
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        service="SecureVault",
        version="1.0.0",
        environment=settings.APP_ENV,
    )


@readiness_router.get(
    "",
    response_model=ReadinessResponse,
)
async def readiness_check():
    checks: list[ReadinessCheck] = [
        await _check_database()
    ]

    failed = [
        c for c in checks
        if c.status == "down"
    ]

    degraded = [
        c for c in checks
        if c.status == "degraded"
    ]

    if failed:
        status = "unhealthy"

    elif degraded:
        status = "degraded"

    else:
        status = "healthy"

    return ReadinessResponse(
        status=status,
        checks=checks,
        checked_at=datetime.now(
            timezone.utc
        ),
    )


async def _check_database() -> ReadinessCheck:

    try:

        with SessionLocal() as db:

            db.execute(
                text("SELECT 1")
            )

        return ReadinessCheck(
            name="database",
            status="ok",
        )

    except Exception as exc:

        detail = (
            str(exc).splitlines()[0]
            if str(exc)
            else "unavailable"
        )

        return ReadinessCheck(
            name="database",
            status="down",
            detail=detail,
        )