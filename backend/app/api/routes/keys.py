from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from uuid import UUID

from app.api.dependencies.current_user import (
    get_current_user,
)

from app.api.dependencies.storage import (
    get_audit_service,
    get_key_management_service,
)

from app.domain.constants.audit_events import (
    KEY_GENERATED,
    KEY_REVOKED,
    KEY_ROTATED,
)

from app.schemas.key_management import (
    KeyCreateRequest,
    KeyCreateResponse,
    KeyResponse,
    KeyRevokeResponse,
    KeyRotateRequest,
    KeyRotateResponse,
    PaginatedKeysResponse,
)

from app.services.audit_service import AuditService
from app.services.key_management_service import (
    KeyManagementService,
    KeyNotFoundError,
)

router = APIRouter(
    prefix="/keys",
    tags=["Keys"],
)


def _key_response(
    key,
) -> KeyResponse:

    return KeyResponse(
        id=key.id,
        created_at=key.created_at,
        updated_at=key.updated_at,
        name=key.name,
        algorithm=key.algorithm,
        key_size=key.key_size,
        status=key.status,
        fingerprint=key.fingerprint,
        expires_at=key.expires_at,
        revoked_at=key.revoked_at,
        replaced_by_key_id=(
            key.replaced_by_key_id
            if hasattr(
                key,
                "replaced_by_key_id",
            )
            else None
        ),
    )


def _public_key_create_response(
    key,
) -> KeyCreateResponse:

    return KeyCreateResponse(
        id=key.id,
        created_at=key.created_at,
        updated_at=key.updated_at,
        name=key.name,
        algorithm=key.algorithm,
        key_size=key.key_size,
        status=key.status,
        fingerprint=key.fingerprint,
        public_key_pem=key.public_key_pem,
        expires_at=key.expires_at,
    )


@router.get(
    "",
    response_model=PaginatedKeysResponse,
)
def list_keys(
    page: int = Query(
        1,
        ge=1,
    ),
    page_size: int = Query(
        20,
        ge=1,
        le=100,
    ),
    status: str | None = Query(
        None,
        pattern="^(active|revoked|expired)$",
    ),
    current_user=Depends(
        get_current_user
    ),
    keys: KeyManagementService = Depends(
        get_key_management_service
    ),
):

    all_keys = keys.list_keys(
        current_user.id,
        status,
    )

    start = (page - 1) * page_size

    items = [
        _key_response(k)
        for k in all_keys[
            start: start + page_size
        ]
    ]

    return PaginatedKeysResponse(
        items=items,
        total=len(all_keys),
        page=page,
        page_size=page_size,
    )


@router.get(
    "/active",
    response_model=KeyResponse,
)
def get_active_key(
    current_user=Depends(
        get_current_user
    ),
    keys: KeyManagementService = Depends(
        get_key_management_service
    ),
):

    try:

        key = keys.get_active_key(
            current_user.id
        )

    except KeyNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return _key_response(key)


@router.get(
    "/{key_id}",
    response_model=KeyResponse,
)
def get_key(
    key_id: UUID,
    current_user=Depends(
        get_current_user
    ),
    keys: KeyManagementService = Depends(
        get_key_management_service
    ),
):

    try:

        key = keys.get_key(
            current_user.id,
            key_id,
        )

    except KeyNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return _key_response(key)


@router.post(
    "",
    response_model=KeyCreateResponse,
    status_code=201,
)
def generate_key(
    payload: KeyCreateRequest,
    current_user=Depends(
        get_current_user
    ),
    keys: KeyManagementService = Depends(
        get_key_management_service
    ),
    audit: AuditService = Depends(
        get_audit_service
    ),
):

    key = keys.generate_key_pair(
        current_user.id,
        payload.name,
        payload.validity_days,
    )

    audit.log(
        current_user.id,
        KEY_GENERATED,
        f"key={key.id}",
    )

    return _public_key_create_response(key)


@router.post(
    "/rotate",
    response_model=KeyRotateResponse,
)
def rotate_key(
    payload: KeyRotateRequest,
    current_user=Depends(
        get_current_user
    ),
    keys: KeyManagementService = Depends(
        get_key_management_service
    ),
    audit: AuditService = Depends(
        get_audit_service
    ),
):

    try:

        old_key, new_key = keys.rotate_key(
            current_user.id,
            payload.current_key_id,
            payload.name,
            payload.validity_days,
        )

    except KeyNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    audit.log(
        current_user.id,
        KEY_ROTATED,
        f"old={old_key.id} new={new_key.id}",
    )

    return KeyRotateResponse(
        old_key=_key_response(old_key),
        new_key=_public_key_create_response(new_key),
    )


@router.post(
    "/{key_id}/revoke",
    response_model=KeyRevokeResponse,
)
def revoke_key(
    key_id: UUID,
    current_user=Depends(
        get_current_user
    ),
    keys: KeyManagementService = Depends(
        get_key_management_service
    ),
    audit: AuditService = Depends(
        get_audit_service
    ),
):

    try:

        key = keys.revoke_key(
            current_user.id,
            key_id,
        )

    except KeyNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    audit.log(
        current_user.id,
        KEY_REVOKED,
        f"key={key.id}",
    )

    return KeyRevokeResponse(
        key_id=key.id,
        revoked=True,
        revoked_at=key.revoked_at,
    )