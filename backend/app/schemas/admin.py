from pydantic import BaseModel

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


class StorageUsageResponse(BaseModel):
    storage_bytes: int
    stored_file_count: int
    temp_file_count: int


class GarbageCollectionResult(BaseModel):
    orphaned_containers: int
    missing_records: int
    purged_deleted: int
    temp_files: int