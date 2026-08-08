from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.dependencies.database import (
    get_db,
)

from app.api.dependencies.repositories import (
    get_audit_repository,
    get_crypto_key_repository,
    get_password_reset_token_repository,
    get_refresh_token_repository,
    get_session_repository,
    get_stored_file_repository,
    get_user_repository,
)

from app.services.audit_service import (
    AuditService,
)

from app.services.auth.email_service import (
    EmailService,
)

from app.services.auth.password_reset_service import (
    PasswordResetService,
)

from app.services.auth.pwned_service import (
    PwnedPasswordChecker,
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

from app.services.storage.quota_service import (
    QuotaService,
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


def get_quota_service(
    stored_files=Depends(
        get_stored_file_repository
    ),
) -> QuotaService:

    return QuotaService(
        stored_files
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
    quota_service=Depends(
        get_quota_service
    ),
) -> UploadService:

    return UploadService(
        storage,
        stored_files,
        keys,
        quota_service=quota_service,
    )


def get_email_service() -> EmailService:

    return EmailService()


def get_pwned_checker() -> PwnedPasswordChecker:

    return PwnedPasswordChecker()


def get_password_reset_service(
    user_repository=Depends(
        get_user_repository
    ),
    token_repository=Depends(
        get_password_reset_token_repository
    ),
    session_repository=Depends(
        get_session_repository
    ),
    refresh_repository=Depends(
        get_refresh_token_repository
    ),
    audit_repository=Depends(
        get_audit_repository
    ),
    email_service=Depends(
        get_email_service
    ),
    pwned=Depends(
        get_pwned_checker
    ),
) -> PasswordResetService:

    return PasswordResetService(
        user_repository,
        token_repository,
        session_repository,
        refresh_repository,
        audit_repository,
        email_service,
        pwned,
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


def get_data_retention_service(
    audit_repository=Depends(
        get_audit_repository
    ),
    session_repository=Depends(
        get_session_repository
    ),
    refresh_repository=Depends(
        get_refresh_token_repository
    ),
    reset_repository=Depends(
        get_password_reset_token_repository
    ),
    verification_repository=Depends(
        get_email_verification_token_repository
    ),
):

    from app.services.data_retention_service import (
        DataRetentionService,
    )

    return DataRetentionService(
        audit_repository,
        session_repository,
        refresh_repository,
        reset_repository,
        verification_repository,
    )


def get_garbage_collector(
    storage=Depends(
        get_storage_service
    ),
    stored_files=Depends(
        get_stored_file_repository
    ),
    retention=Depends(
        get_data_retention_service
    ),
) -> GarbageCollector:

    return GarbageCollector(
        storage,
        stored_files,
        retention_service=retention,
    )


def get_db_for_service(
    db: Session = Depends(get_db),
) -> Session:
    return db