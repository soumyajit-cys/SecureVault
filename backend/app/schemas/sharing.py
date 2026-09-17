from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class ShareCreateRequest(BaseModel):
    grantee_email: EmailStr


class ShareResponse(BaseModel):
    id: UUID
    file_id: UUID
    owner_id: UUID
    grantee_id: UUID
    grantee_key_id: UUID | None = None
    key_algorithm: str
    created_at: datetime
    updated_at: datetime
    revoked_at: datetime | None = None


class SharedFileItem(BaseModel):
    share: ShareResponse
    file_id: UUID
    original_filename: str
    mime_type: str
    original_size: int
    encrypted_size: int
    sha256: str
    is_folder: bool
    owner_id: UUID
