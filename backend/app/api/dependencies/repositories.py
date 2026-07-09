from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.dependencies.database import (
    get_db,
)

from app.infrastructure.repositories.audit_log_repository import (
    SQLAlchemyAuditLogRepository,
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