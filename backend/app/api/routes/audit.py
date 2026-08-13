from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import Request

from fastapi.responses import StreamingResponse

from app.api.dependencies.current_user import (
    get_current_user,
)

from app.api.dependencies.rbac import (
    require_privileged_mfa,
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
    mfa_guard=Depends(
        require_privileged_mfa
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


@router.get(
    "/admin/export",
)
def export_audit_logs(
    action: str | None = Query(None),
    current_user=Depends(
        require_role("Admin")
    ),
    mfa_guard=Depends(
        require_privileged_mfa
    ),
    audit: AuditService = Depends(
        get_audit_service
    ),
):
    """
    Full CSV export of the global audit trail.
    """

    items = audit.repository.list_all_unpaginated(
        action=action
    )

    from app.domain.constants.audit_events import (
        AUDIT_EXPORTED,
    )

    audit.log(
        current_user.id,
        AUDIT_EXPORTED,
        (
            f"exported {len(items)} audit records "
            f"action={action or 'all'}"
        ),
    )

    def rows():

        yield (
            "id,created_at,user_id,action,"
            "resource_type,resource_id,details\n"
        )

        for item in items:

            user_id = (
                str(item.user_id)
                if item.user_id
                else ""
            )

            resource_id = (
                str(item.resource_id)
                if item.resource_id
                else ""
            )

            details = (
                (item.details or "")
                .replace('"', '""')
            )

            yield (
                f"{item.id},"
                f"{item.created_at.isoformat()},"
                f"{user_id},"
                f"{item.action},"
                f"{item.resource_type or ''},"
                f"{resource_id},"
                f'"{details}"\n'
            )

    return StreamingResponse(
        rows(),
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                'attachment; '
                'filename="audit-log.csv"'
            )
        },
    )