from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import UploadFile
from fastapi import File

from app.api.dependencies.current_user import (
    get_current_user,
)

from app.api.dependencies.storage import (
    get_audit_service,
    get_download_service,
    get_key_management_service,
    get_storage_service,
    get_upload_service,
)

from app.core.exceptions import NotFoundError
from app.domain.constants.audit_events import (
    FOLDER_DECRYPTED,
    FOLDER_ENCRYPTED,
)

from app.schemas.storage import (
    FolderRestoreResponse,
    FolderUploadResponse,
)

from app.services.audit_service import AuditService
from app.services.key_management_service import (
    KeyNotFoundError,
)
from app.services.storage.download_service import (
    DownloadService,
)
from app.services.storage.storage_service import (
    StorageService,
)
from app.services.storage.upload_service import (
    UploadService,
)

router = APIRouter(
    prefix="/folders",
    tags=["Folders"],
)


@router.post(
    "/upload",
    response_model=FolderUploadResponse,
    status_code=201,
)
async def upload_folder(
    upload: UploadFile = File(...),
    current_user=Depends(
        get_current_user
    ),
    uploads: UploadService = Depends(
        get_upload_service
    ),
    storage: StorageService = Depends(
        get_storage_service
    ),
    keys=Depends(
        get_key_management_service
    ),
    audit: AuditService = Depends(
        get_audit_service
    ),
):

    from app.services.encryption.folder_archiver import (
        FolderArchiver,
    )

    if not (
        upload.content_type == "application/zip"
        or (upload.filename or "").endswith(".zip")
    ):
        raise HTTPException(
            status_code=422,
            detail="Folder uploads must be ZIP archives.",
        )

    temp = storage.create_temp_path(
        suffix=".zip"
    )

    extract_dir = storage.vault_dir_for(
        "folder-unpack"
    )

    try:

        with temp.open("wb") as out:

            while True:

                chunk = await upload.read(1024 * 1024)

                if not chunk:
                    break

                out.write(chunk)

        FolderArchiver().extract_archive(
            temp,
            extract_dir,
        )

        key = keys.get_active_key(
            current_user.id
        )

        stored = uploads.upload_folder(
            current_user.id,
            key,
            extract_dir,
        )

    except KeyNotFoundError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Folder upload failed: {exc}",
        ) from exc

    finally:

        storage.remove(temp)

        storage.remove(extract_dir)

    audit.log(
        current_user.id,
        FOLDER_ENCRYPTED,
        (
            "folder={} "
            "files={}"
        ).format(
            stored.id,
            stored.folder_file_count,
        ),
        resource_type="stored_folder",
        resource_id=str(stored.id),
    )

    return FolderUploadResponse(
        file_id=str(stored.id),
        folder_name=stored.original_filename,
        file_count=stored.folder_file_count,
        encrypted_size=stored.encrypted_size,
        sha256=stored.sha256,
        created_at=stored.created_at.isoformat(),
    )


@router.post(
    "/{file_id}/restore",
    response_model=FolderRestoreResponse,
)
def restore_folder(
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

        if not file.is_folder:
            raise HTTPException(
                status_code=422,
                detail="Stored file is not a folder.",
            )

        key = keys.get_key(
            current_user.id,
            file.key_id,
        )

        restored = downloads.restore_folder(
            file,
            key,
        )

    except (NotFoundError, KeyNotFoundError) as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Folder restore failed: {exc}",
        ) from exc

    audit.log(
        current_user.id,
        FOLDER_DECRYPTED,
        f"folder={file.id}",
        resource_type="stored_folder",
        resource_id=str(file.id),
    )

    return FolderRestoreResponse(
        file_id=str(file.id),
        restored_path=str(restored),
        restored_files=sum(
            1
            for p in restored.rglob("*")
            if p.is_file()
        ),
        restored_directories=sum(
            1
            for p in restored.rglob("*")
            if p.is_dir()
        ),
    )