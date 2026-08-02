from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import TimestampSchema


class StoredFileResponse(TimestampSchema):
    user_id: UUID
    key_id: UUID | None = None

    original_filename: str
    mime_type: str

    original_size: int
    encrypted_size: int
    sha256: str

    is_folder: bool
    folder_file_count: int

    status: str
    deleted_at: datetime | None = None


class PaginatedStoredFilesResponse(BaseModel):
    items: list[StoredFileResponse]
    total: int
    page: int
    page_size: int


class StoredFileListParams(BaseModel):
    page: int = 1
    page_size: int = 20
    status: str | None = None
    mime_type: str | None = None
    is_folder: bool | None = None
    search: str | None = None


class RenameFileRequest(BaseModel):
    new_name: str


class FolderUploadResponse(BaseModel):
    file_id: str

    folder_name: str

    file_count: int

    encrypted_size: int

    sha256: str

    created_at: str


class FolderRestoreResponse(BaseModel):
    file_id: str

    restored_path: str

    restored_files: int

    restored_directories: int


class StorageSummaryResponse(BaseModel):
    file_count: int
    folder_count: int
    encrypted_bytes: int
    original_bytes: int