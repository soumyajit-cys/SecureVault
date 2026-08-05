from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from uuid import UUID

from app.api.dependencies.current_user import (
    get_current_user,
)
from app.api.dependencies.rbac import (
    require_role,
)
from app.api.dependencies.repositories import (
    get_user_repository,
)

from app.api.dependencies.storage import (
    get_audit_service,
    get_garbage_collector,
    get_quota_service,
    get_storage_service,
)

from app.schemas.admin import (
    AdminUserCreateRequest,
    AdminUserDetailResponse,
    AdminUserRolesRequest,
    AdminUserUpdateRequest,
    GarbageCollectionResult,
    PaginatedUsersResponse,
    StorageUsageResponse,
)

from app.schemas.user import (
    UserResponse,
)

from app.core.exceptions import (
    NotFoundError,
    UserAlreadyExistsError,
)

from app.domain.constants.audit_events import (
    ADMIN_ACTION,
)

from app.services.audit_service import (
    AuditService,
)

from app.services.auth.admin_user_service import (
    AdminUserService,
)

from app.services.storage.garbage_collector import (
    GarbageCollector,
)

from app.services.storage.quota_service import (
    QuotaService,
)

from app.services.storage.storage_service import (
    StorageService,
)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


def _user_response(user) -> UserResponse:

    return UserResponse(
        id=user.id,
        created_at=user.created_at,
        updated_at=user.updated_at,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        is_verified=user.is_verified,
        failed_login_attempts=user.failed_login_attempts,
        locked_until=user.locked_until,
        roles=[
            {
                "id": str(ur.role.id),
                "name": ur.role.name,
            }
            for ur in user.roles
        ],
    )


@router.get("/status")
def admin_status(
    user=Depends(
        require_role(
            "Admin"
        )
    ),
):
    return {
        "status": "ok"
    }


@router.get(
    "/users",
    response_model=PaginatedUsersResponse,
)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user=Depends(
        require_role(
            "Admin"
        )
    ),
    users=Depends(
        get_user_repository
    ),
):

    items, total = users.list_all(
        page,
        page_size,
    )

    return PaginatedUsersResponse(
        items=[
            _user_response(u)
            for u in items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/users/{user_id}/activate",
)
def activate_user(
    user_id: UUID,
    user=Depends(
        require_role(
            "Admin"
        )
    ),
    users=Depends(
        get_user_repository
    ),
    current=Depends(
        get_current_user
    ),
    audit: AuditService = Depends(
        get_audit_service
    ),
):

    target = users.get(user_id)

    if not target:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    target.is_active = True
    target.failed_login_attempts = 0
    target.locked_until = None

    users.update(target)

    audit.log(
        current.id,
        ADMIN_ACTION,
        f"activated user={target.id}",
        resource_type="user",
        resource_id=str(target.id),
    )

    return {"message": "User activated"}


@router.post(
    "/users/{user_id}/deactivate",
)
def deactivate_user(
    user_id: UUID,
    user=Depends(
        require_role(
            "Admin"
        )
    ),
    users=Depends(
        get_user_repository
    ),
    current=Depends(
        get_current_user
    ),
    audit: AuditService = Depends(
        get_audit_service
    ),
):

    if user_id == current.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot deactivate your own account",
        )

    target = users.get(user_id)

    if not target:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    target.is_active = False

    users.update(target)

    audit.log(
        current.id,
        ADMIN_ACTION,
        f"user={target.id} deactivated",
        resource_type="user",
        resource_id=str(target.id),
    )

    return {"message": "User deactivated"}


@router.get(
    "/storage",
    response_model=StorageUsageResponse,
)
def storage_usage(
    user=Depends(
        require_role(
            "Admin"
        )
    ),
    storage: StorageService = Depends(
        get_storage_service
    ),
):

    containers = list(
        storage.iter_containers()
    )

    return StorageUsageResponse(
        storage_bytes=sum(
            c.stat().st_size
            for c in containers
        ),
        stored_file_count=len(
            containers
        ),
        temp_file_count=sum(
            1
            for t in storage.temp_dir.iterdir()
            if t.is_file()
        ),
    )


@router.post(
    "/garbage-collect",
    response_model=GarbageCollectionResult,
)
def garbage_collect(
    user=Depends(
        require_role(
            "Admin"
        )
    ),
    collector: GarbageCollector = Depends(
        get_garbage_collector
    ),
):

    summary = collector.run_all()

    return GarbageCollectionResult(
        orphaned_containers=summary["orphaned_containers"],
        missing_records=summary["missing_records"],
        purged_deleted=summary["purged_deleted"],
        temp_files=summary["temp_files"],
    )