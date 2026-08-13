from fastapi import APIRouter
from fastapi import Depends

from app.api.dependencies.current_user import (
    get_current_user,
)
from app.api.dependencies.storage import (
    get_quota_service,
)
from app.services.storage.quota_service import (
    QuotaService,
)

router = APIRouter(
    prefix="/profile",
    tags=["Profile"],
)


@router.get("/me")
def me(
    current_user=Depends(
        get_current_user
    ),
):
    return {
        "id": str(
            current_user.id
        ),
        "email": current_user.email,
        "username": current_user.username,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "mfa_enabled": bool(
            current_user.totp_enabled
        ),
        "roles": [
            {
                "id": str(
                    user_role.role.id
                ),
                "name": (
                    user_role.role.name
                ),
            }
            for user_role
            in current_user.roles
            if user_role.role is not None
        ],
    }


@router.get("/quota")
def my_quota(
    current_user=Depends(
        get_current_user
    ),
    quota: QuotaService = Depends(
        get_quota_service
    ),
):

    usage = quota.usage(
        current_user.id
    )

    limit = (
        current_user.storage_quota_bytes
    )

    return {
        "storage_quota_bytes": limit,
        "storage_usage_bytes": usage,
        "remaining_bytes": (
            max(limit - usage, 0)
            if limit is not None
            else None
        ),
    }