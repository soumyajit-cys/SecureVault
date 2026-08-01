from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import Field

from app.schemas.common import TimestampSchema


class KeyCreateRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
        description="Human readable key name.",
    )

    validity_days: int = Field(
        default=365,
        ge=1,
        le=3650,
        description=(
            "Lifetime of the key in days "
            "before it expires."
        ),
    )


class KeyCreateResponse(TimestampSchema):
    name: str
    algorithm: str
    key_size: int
    status: str
    fingerprint: str
    public_key_pem: str
    expires_at: datetime | None = None


class KeyResponse(TimestampSchema):
    name: str
    algorithm: str
    key_size: int
    status: str
    fingerprint: str
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    replaced_by_key_id: UUID | None = None


class KeyRotateRequest(BaseModel):
    current_key_id: UUID

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    validity_days: int = Field(
        default=365,
        ge=1,
        le=3650,
    )


class KeyRotateResponse(BaseModel):
    old_key: KeyResponse
    new_key: KeyCreateResponse


class KeyRevokeResponse(BaseModel):
    key_id: UUID
    revoked: bool
    revoked_at: datetime


class KeyStatusUpdateResponse(BaseModel):
    expired: int


class PaginatedKeysResponse(BaseModel):
    items: list[KeyResponse]
    total: int
    page: int
    page_size: int
