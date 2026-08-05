from datetime import datetime

from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import Field

from app.schemas.audit import AuditLogResponse
from app.schemas.user import UserResponse


class PaginatedAuditResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int


class PaginatedUsersResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    page_size: int


class AdminUserCreateRequest(BaseModel):
    email: EmailStr
    username: str = Field(
        min_length=3,
        max_length=100,
    )
    password: str = Field(
        min_length=12,
        max_length=128,
    )
    roles: list[str] = []
    storage_quota_bytes: int | None = Field(
        default=None,
        ge=0,
    )


class AdminUserUpdateRequest(BaseModel):
    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=100,
    )
    is_active: bool | None = None
    storage_quota_bytes: int | None = Field(
        default=None,
        ge=0,
    )


class AdminUserRolesRequest(BaseModel):
    roles: list[str]


class AdminUserDetailResponse(UserResponse):
    storage_quota_bytes: int | None = None

    storage_usage_bytes: int = 0


class UserQuotaResponse(BaseModel):
    storage_quota_bytes: int | None

    storage_usage_bytes: int

    remaining_bytes: int | None


class StorageUsageResponse(BaseModel):
    storage_bytes: int
    stored_file_count: int
    temp_file_count: int


class GarbageCollectionResult(BaseModel):
    orphaned_containers: int
    missing_records: int
    purged_deleted: int
    temp_files: int