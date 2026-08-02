from fastapi import APIRouter

from app.api.routes.admin import (
    router as admin_router
)

from app.api.routes.audit import (
    router as audit_router
)

from app.api.routes.auth import (
    router as auth_router
)

from app.api.routes.encryption import (
    router as encryption_router
)

from app.api.routes.files import (
    router as files_router
)

from app.api.routes.folders import (
    router as folders_router
)

from app.api.routes.health import (
    router as health_router
)

from app.api.routes.health import (
    liveness_router
)

from app.api.routes.health import (
    readiness_router
)

from app.api.routes.keys import (
    router as keys_router
)

from app.api.routes.metrics import (
    router as metrics_router
)

from app.api.routes.profile import (
    router as profile_router
)

api_router = APIRouter()

api_router.include_router(
    admin_router
)

api_router.include_router(
    audit_router
)

api_router.include_router(
    auth_router
)

api_router.include_router(
    encryption_router
)

api_router.include_router(
    files_router
)

api_router.include_router(
    folders_router
)

api_router.include_router(
    health_router
)

api_router.include_router(
    liveness_router
)

api_router.include_router(
    readiness_router
)

api_router.include_router(
    keys_router
)

api_router.include_router(
    metrics_router
)

api_router.include_router(
    profile_router
)