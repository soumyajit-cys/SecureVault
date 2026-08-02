from io import BytesIO
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import UploadFile
from fastapi import File
from fastapi.responses import StreamingResponse

from app.api.dependencies.current_user import (
    get_current_user,
)

from app.api.dependencies.storage import (
    get_audit_service,
    get_download_service,
    get_key_management_service,
    get_metadata_service,
    get_upload_service,
)

from app.core.exceptions import (
    FileTooLargeError,
    NotFoundError,
)

from app.domain.constants.audit_events import (
    FILE_DELETED,
    FILE_DOWNLOADED,
    FILE_ENCRYPTED,
    FILE_UPLOADED,
)

from app.schemas.encryption import (
    EncryptFileResponse,
)

from app.schemas.storage import (
    PaginatedStoredFilesResponse,
    RenameFileRequest,
    StoredFileResponse,
)

from app.services.audit_service import AuditService
from app.services.key_management_service import (
    KeyNotFoundError,
)
from app.services.storage.download_service import (
    DownloadService,
)
from app.services.storage.metadata_service import (
    MetadataService,
)
from app.services.storage.upload_service import (
    UploadService,
)

router = APIRouter(
    prefix="/files",
    tags=["Files"],
)


def _file_response(
    file,
) -> StoredFileResponse:

    return StoredFileResponse(
        id=file.id,
        created_at=file.created_at,
        updated_at=file.updated_at,
        user_id=file.user_id,
        key_id=file.key_id,
        original_filename=file.original_filename,
        mime_type=file.mime_type,
        original_size=file.original_size,
        encrypted_size=file.encrypted_size,
        sha256=file.sha256,
        is_folder=file.is_folder,
        folder_file_count=file.folder_file_count,
        status=file.status,
        deleted_at=file.deleted_at,
    )


@router.post(
    "/upload",
    response_model=EncryptFileResponse,
    status_code=201,
)
async def upload_file(
    upload: UploadFile = File(...),
    current_user=Depends(
        get_current_user
    ),
    uploads: UploadService = Depends(
        get_upload_service
    ),
    keys=Depends(
        get_key_management_service
    ),
    audit: AuditService = Depends(
        get_audit_service
    ),
):

    try:

        key = keys.get_active_key(
            current_user.id
        )

        stored = uploads.upload_file(
            current_user.id,
            key,
            upload.file,
            filename=upload.filename,
            mime_type=upload.content_type,
        )

    except KeyNotFoundError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except FileTooLargeError as exc:
        raise HTTPException(
            status_code=413,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {exc}",
        ) from exc

    audit.log(
        current_user.id,
        FILE_UPLOADED,
        f"file={stored_id(stored)} name={stored.original_filename}",
        resource_type="file",
        resource_id=str(stored.id),
    )

    return _file_response(stored)


import app.main  # noqa: F401


@router.get(
    "",
    response_model=PaginatedStoredFilesResponse,
)
def list_files(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    mime_type: str | None = Query(None),
    is_folder: bool | None = Query(None),
    search: str | None = Query(None),
    current_user=Depends(
        get_current_user
    ),
    metadata: MetadataService = Depends(
        get_metadata_service
    ),
):

    items, total = metadata.list(
        current_user.id,
        page=page,
        page_size=page_size,
        status=status,
        mime_type=mime_type,
        is_folder=is_folder,
        search=search,
    )

    return PaginatedStoredFilesResponse(
        items=[
            _file_response(f)
            for f in items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{file_id}",
    response_model=StoredFileResponse,
)
def get_file(
    file_id: UUID,
    current_user=Depends(
        get_current_user
    ),
    metadata: MetadataService = Depends(
        get_metadata_service
    ),
):

    try:

        file = metadata.get(
            current_user.id,
            file_id,
        )

    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return _file_response(file)


@router.get(
    "/{file_id}/download",
)
def download_file(
    file_id: UUID,
    current_user=Depends(
        get_current_user
    ),
    downloads: DownloadService = Depends(
        get_download_service
    ),
    keys=Depends(
        get_key_management_service
    ),
    audit: AuditService = Depends(
        get_audit_service
    ),
):

    try:

        file = downloads.get_for_user(
            current_user.id,
            file_id,
        )

        key = keys.get_key(
            current_user.id,
            file.key_id,
        )

        media_type = (
            file.mime_type
            or "application/octet-stream"
        )

        def packet():

            sha256, chunks = (
                downloads.stream_decrypted(
                    file,
                    key,
                    (yield_through := BytesIOWriterChunk()),
                )
            )

    except (NotFoundError, KeyNotFoundError) as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return StreamingResponse(
        output_stream(
            downloads,
            file,
            key,
        ),
        media_type=media_type,
        headers={
            "Content-Disposition": (
                f'attachment; filename="{file.original_filename}"'
            ),
            "X-SHA256": file.sha256,
        },
    )


@router.delete(
    "/{file_id}",
    status_code=204,
)
def delete_file(
    file_id: UUID,
    current_user=Depends(
        get_current_user
    ),
    metadata: MetadataService = Depends(
        get_metadata_service
    ),
    audit: AuditService = Depends(
        get_audit_service
    ),
):

    try:

        file = metadata.soft_delete(
            current_user.id,
            file_id,
        )

    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    audit.log(
        current_user.id,
        FILE_DELETED,
        f"file={file.id}",
        resource_type="stored_file",
        resource_id=str(file.id),
    )


@router.patch(
    "/{file_id}",
    response_model=StoredFileResponse,
)
def rename_file(
    file_id: UUID,
    payload: RenameFileRequest,
    current_user=Depends(
        get_current_user
    ),
    metadata: MetadataService = Depends(
        get_metadata_service
    ),
):

    try:

        file = metadata.rename(
            current_user.id,
            file_id,
            payload.new_name,
        )

    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return _file_response(file)