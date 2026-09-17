from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from app.api.dependencies.current_user import (
    get_current_user,
)
from app.api.dependencies.permissions import (
    require_permission,
)
from app.api.dependencies.storage import (
    get_audit_service,
    get_file_share_service,
)
from app.domain.constants.audit_events import (
    FILE_SHARED,
    FILE_SHARE_REVOKED,
)
from app.schemas.sharing import (
    ShareCreateRequest,
    SharedFileItem,
    ShareResponse,
)
from app.services.audit_service import AuditService
from app.services.file_share_service import (
    ShareError,
    ShareNotFoundError,
    ShareService,
)

router = APIRouter(
    prefix="/shares",
    tags=["Sharing"],
)


def _share_response(grant) -> ShareResponse:
    return ShareResponse(
        id=grant.id,
        file_id=grant.file_id,
        owner_id=grant.owner_id,
        grantee_id=grant.grantee_id,
        grantee_key_id=grant.grantee_key_id,
        key_algorithm=grant.key_algorithm,
        created_at=grant.created_at,
        updated_at=grant.updated_at,
        revoked_at=grant.revoked_at,
    )


@router.post(
    "/files/{file_id}/share",
    response_model=ShareResponse,
    status_code=201,
)
def share_file(
    file_id: UUID,
    payload: ShareCreateRequest,
    current_user=Depends(
        require_permission("share:create")
    ),
    shares: ShareService = Depends(
        get_file_share_service
    ),
    audit: AuditService = Depends(
        get_audit_service
    ),
):
    try:
        grant = shares.share(
            current_user.id,
            file_id,
            str(payload.grantee_email),
        )
    except ShareNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ShareError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    audit.log(
        current_user.id,
        FILE_SHARED,
        (
            f"file={grant.file_id} "
            f"grantee={grant.grantee_id} "
            f"share={grant.id}"
        ),
        resource_type="stored_file",
        resource_id=str(grant.file_id),
    )

    # 200 on idempotent replay would be friendlier, but 201 keeps
    # the contract simple; the body identifies the existing grant.
    return _share_response(grant)


@router.delete(
    "/files/{file_id}/shares/{grantee_id}",
    status_code=204,
)
def revoke_share(
    file_id: UUID,
    grantee_id: UUID,
    current_user=Depends(
        require_permission("share:revoke")
    ),
    shares: ShareService = Depends(
        get_file_share_service
    ),
    audit: AuditService = Depends(
        get_audit_service
    ),
):
    try:
        grant = shares.revoke(
            current_user.id,
            file_id,
            grantee_id,
        )
    except ShareNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ShareError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    audit.log(
        current_user.id,
        FILE_SHARE_REVOKED,
        (
            f"file={grant.file_id} "
            f"grantee={grant.grantee_id} "
            f"share={grant.id}"
        ),
        resource_type="stored_file",
        resource_id=str(grant.file_id),
    )


@router.get(
    "/files/{file_id}/shares",
    response_model=list[ShareResponse],
)
def list_file_shares(
    file_id: UUID,
    current_user=Depends(get_current_user),
    shares: ShareService = Depends(
        get_file_share_service
    ),
):
    try:
        _, grants = shares.list_for_file(
            current_user.id,
            file_id,
        )
    except ShareNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return [_share_response(g) for g in grants]


@router.get(
    "/received",
    response_model=list[SharedFileItem],
)
def list_received_shares(
    current_user=Depends(get_current_user),
    shares: ShareService = Depends(
        get_file_share_service
    ),
):
    pairs = shares.list_received(
        current_user.id
    )

    items: list[SharedFileItem] = []

    for grant, stored in pairs:
        items.append(
            SharedFileItem(
                share=_share_response(grant),
                file_id=stored.id,
                original_filename=(
                    stored.original_filename
                ),
                mime_type=stored.mime_type,
                original_size=stored.original_size,
                encrypted_size=stored.encrypted_size,
                sha256=stored.sha256,
                is_folder=stored.is_folder,
                owner_id=stored.user_id,
            )
        )

    return items


@router.get(
    "/sent",
    response_model=list[ShareResponse],
)
def list_sent_shares(
    current_user=Depends(get_current_user),
    shares: ShareService = Depends(
        get_file_share_service
    ),
):
    grants = shares.list_sent(
        current_user.id
    )

    return [_share_response(g) for g in grants]
