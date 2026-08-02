from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.dependencies.database import (
    get_db,
)

from app.api.dependencies.repositories import (
    get_audit_repository,
    get_crypto_key_repository,
    get_stored_file_repository,
)

from app.services.audit_service import (
    AuditService,
)

from app.services.crypto_service import (
    CryptoService,
)

from app.services.key_management_service import (
    KeyManagementService,
)

from app.services.storage.download_service import (
    DownloadService,
)

from app.services.storage.garbage_collector import (
    GarbageCollector,
)

from app.services.storage.metadata_service import (
    MetadataService,
)

from app.services.storage.storage_service import (
    StorageService,
)

from app.services.storage.upload_service import (
    UploadService,
)


def get_storage_service() -> StorageService:
    return StorageService()


def get_key_management_service(
    key_repository=Depends(
        get_crypto_key_repository
    ),
) -> KeyManagementService:

    return KeyManagementService(
        key_repository
    )


def get_crypto_service(
    keys=Depends(
        get_key_management_service
    ),
) -> CryptoService:

    return CryptoService(
        keys
    )


def get_upload_service(
    storage=Depends(
        get_storage_service
    ),
    stored_files=Depends(
        get_stored_file_repository
    ),
    keys=Depends(
        get_key_management_service
    ),
) -> UploadService:

    return UploadService(
        storage,
        stored_files,
        keys,
    )


def get_download_service(
    storage=Depends(
        get_storage_service
    ),
    stored_files=Depends(
        get_stored_file_repository
    ),
    keys=Depends(
        get_key_management_service
    ),
) -> DownloadService:

    return DownloadService(
        storage,
        stored_files,
        keys,
    )


def get_metadata_service(
    storage=Depends(
        get_storage_service
    ),
    stored_files=Depends(
        get_stored_file_repository
    ),
) -> MetadataService:

    return MetadataService(
        storage,
        stored_files,
    )


def get_audit_service(
    audit_repository=Depends(
        get_audit_repository
    ),
) -> AuditService:

    return AuditService(
        audit_repository
    )


def get_garbage_collector(
    storage=Depends(
        get_storage_service
    ),
    stored_files=Depends(
        get_stored_file_repository
    ),
) -> GarbageCollector:

    return GarbageCollector(
        storage,
        stored_files,
    )


def get_db_for_service(
    db: Session = Depends(get_db),
) -> Session:
    return db