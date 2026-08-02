from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domain.constants.audit_events import (
    USER_REGISTERED,
)
from app.domain.models.role import (
    Role,
)
from app.domain.models.user import (
    User,
)
from app.domain.models.user_role import (
    UserRole,
)
from app.domain.constants.auth import (
    ADMIN_ROLE,
)
from app.services.audit_service import (
    AuditService,
)
from app.services.auth.password_service import (
    Argon2PasswordService,
)
from app.infrastructure.repositories.audit_log_repository import (
    SQLAlchemyAuditLogRepository,
)


def seed_bootstrap_admin(
    db: Session,
) -> User | None:
    """
    Create the initial administrator account from configuration.

    Reads ``VAULT_ADMIN_EMAIL`` / ``VAULT_ADMIN_USERNAME`` /
    ``VAULT_ADMIN_PASSWORD`` from the environment. When set and no user
    owns that email yet, an account with the ``Admin`` role is created.
    """

    settings = get_settings()

    email = settings.VAULT_ADMIN_EMAIL

    if not email:
        return None

    existing = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing:
        return None

    admin_role = (
        db.query(Role)
        .filter(Role.name == ADMIN_ROLE)
        .first()
    )

    password_service = Argon2PasswordService()

    user = User(
        email=email,
        username=settings.VAULT_ADMIN_USERNAME or "admin",
        password_hash=password_service.hash_password(
            settings.VAULT_ADMIN_PASSWORD
        ),
    )

    db.add(user)
    db.flush()

    if admin_role:
        user.roles.append(
            UserRole(role=admin_role)
        )

    db.commit()
    db.refresh(user)

    audit_repository = (
        SQLAlchemyAuditLogRepository(db)
    )

    AuditService(
        audit_repository
    ).log(
        user.id,
        USER_REGISTERED,
        "bootstrap admin account",
        resource_type="user",
        resource_id=str(user.id),
    )

    return user