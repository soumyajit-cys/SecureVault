from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.dependencies.database import (
    get_db,
)

from app.infrastructure.repositories.audit_log_repository import (
    SQLAlchemyAuditLogRepository,
)
from app.infrastructure.repositories.crypto_key_repository import (
    SQLAlchemyCryptoKeyRepository,
)
from app.infrastructure.repositories.jwt_signing_key_repository import (
    SQLAlchemyJwtSigningKeyRepository,
)
from app.infrastructure.repositories.mfa_recovery_code_repository import (
    SQLAlchemyMfaRecoveryCodeRepository,
)
from app.infrastructure.repositories.password_reset_token_repository import (
    SQLAlchemyPasswordResetTokenRepository,
)
from app.infrastructure.repositories.permission_repository import (
    SQLAlchemyPermissionRepository,
)
from app.infrastructure.repositories.refresh_token_repository import (
    SQLAlchemyRefreshTokenRepository,
)
from app.infrastructure.repositories.role_repository import (
    SQLAlchemyRoleRepository,
)
from app.infrastructure.repositories.session_repository import (
    SQLAlchemySessionRepository,
)
from app.infrastructure.repositories.stored_file_repository import (
    SQLAlchemyStoredFileRepository,
)
from app.infrastructure.repositories.user_repository import (
    SQLAlchemyUserRepository,
)


def get_user_repository(
    db: Session = Depends(get_db),
):
    return SQLAlchemyUserRepository(db)


def get_role_repository(
    db: Session = Depends(get_db),
):
    return SQLAlchemyRoleRepository(db)


def get_permission_repository(
    db: Session = Depends(get_db),
):
    return SQLAlchemyPermissionRepository(
        db
    )


def get_refresh_token_repository(
    db: Session = Depends(get_db),
):
    return SQLAlchemyRefreshTokenRepository(
        db
    )


def get_session_repository(
    db: Session = Depends(get_db),
):
    return SQLAlchemySessionRepository(
        db
    )


def get_audit_repository(
    db: Session = Depends(get_db),
):
    return SQLAlchemyAuditLogRepository(
        db
    )


def get_crypto_key_repository(
    db: Session = Depends(get_db),
):
    return SQLAlchemyCryptoKeyRepository(
        db
    )


def get_stored_file_repository(
    db: Session = Depends(get_db),
):
    return SQLAlchemyStoredFileRepository(
        db
    )


def get_jwt_signing_key_repository(
    db: Session = Depends(get_db),
):
    return SQLAlchemyJwtSigningKeyRepository(
        db
    )


def get_password_reset_token_repository(
    db: Session = Depends(get_db),
):
    return SQLAlchemyPasswordResetTokenRepository(
        db
    )


def get_mfa_recovery_code_repository(
    db: Session = Depends(get_db),
):
    return SQLAlchemyMfaRecoveryCodeRepository(
        db
    )