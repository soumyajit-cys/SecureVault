from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query

from app.api.dependencies.current_user import (
    get_current_user,
)

from app.api.dependencies.rbac import (
    require_role,
)

from app.api.dependencies.storage import (
    get_audit_service,
)

from app.schemas.admin import (
    PaginatedAuditResponse,
)

from app.services.audit_service import (
    AuditService,
)

router = APIRouter(
    prefix="/audit",
    tags=["Audit"],
)


@router.get(
    "/logs",
    response_model=PaginatedAuditResponse,
)
def audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: str | None = Query(None),
    current_user=Depends(
        get_current_user
    ),
    audit: AuditService = Depends(
        get_audit_service
    ),
):

    items, total = audit.list_for_user(
        current_user.id,
        page=page,
        page_size=page_size,
        action=action,
    )

    from app.schemas.audit import (
        AuditLogResponse,
    )

    return PaginatedAuditResponse(
        items=[
            AuditLogResponse(
                id=item.id,
                created_at=item.created_at,
                updated_at=item.updated_at,
                action=item.action,
                resource_type=item.resource_type,
                resource_id=item.resource_id,
                details=item.details,
            )
            for item in items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/admin/logs",
    response_model=PaginatedAuditResponse,
)
def all_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: str | None = Query(None),
    current_user=Depends(
        require_role("Admin")
    ),
    audit: AuditService = Depends(
        get_audit_service
    ),
):

    items, total = audit.list_all(
        page=page,
        page_size=page_size,
        action=action,
    )

    from app.schemas.audit import (
        AuditLogResponse,
    )

    return PaginatedAuditResponse(
        items=[
            AuditLogResponse(
                id=item.id,
                created_at=item.created_at,
                updated_at=item.updated_at,
                action=item.action,
                resource_type=item.resource_type,
                resource_id=item.resource_id,
                details=item.details,
            )
            for item in items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )