from uuid import UUID

from app.core.exceptions import (
    NotFoundError,
    UserAlreadyExistsError,
    WeakPasswordError,
)

from app.domain.constants.audit_events import (
    ADMIN_ROLE_ASSIGNED,
    ADMIN_USER_CREATED,
    ADMIN_USER_DELETED,
    ADMIN_USER_UPDATED,
)

from app.domain.models.user import User

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

from app.services.audit_service import (
    AuditService,
)

from app.services.auth.password_policy import (
    PasswordPolicy,
)

from app.services.auth.password_service import (
    Argon2PasswordService,
)

from app.services.auth.pwned_service import (
    PwnedPasswordChecker,
)


class AdminUserService:
    """
    Admin operations on user accounts. Audit events are
    written as the acting admin user.
    """

    def __init__(
        self,
        user_repository: SQLAlchemyUserRepository,
        role_repository: SQLAlchemyRoleRepository,
        session_repository: SQLAlchemySessionRepository,
        refresh_repository: SQLAlchemyRefreshTokenRepository,
        audit_repository,
    ) -> None:

        self.users = user_repository

        self.roles = role_repository

        self.sessions = session_repository

        self.refresh = refresh_repository

        self.audit_service = (
            AuditService(audit_repository)
        )

        self.password_service = (
            Argon2PasswordService()
        )

        self.pwned = (
            PwnedPasswordChecker()
        )

    def create_user(
        self,
        actor: User,
        email: str,
        username: str,
        password: str,
        role_names: list[str],
        storage_quota_bytes: int | None = None,
    ) -> User:

        result = PasswordPolicy.validate(
            password
        )

        if not result.valid:
            raise WeakPasswordError(
                result.message
            )

        self.pwned.assert_not_pwned(
            password
        )

        if self.users.get_by_email(email):
            raise UserAlreadyExistsError(
                "Email already exists"
            )

        if self.users.get_by_username(username):
            raise UserAlreadyExistsError(
                "Username already exists"
            )

        user = User(
            email=email,
            username=username,
            password_hash=(
                self.password_service
                .hash_password(password)
            ),
            storage_quota_bytes=(
                storage_quota_bytes
            ),
        )

        self.users.create(user)

        self._assign_roles(user, role_names)

        self.audit_service.log(
            actor.id,
            ADMIN_USER_CREATED,
            (
                f"created user={user.id} "
                f"email={user.email}"
            ),
            resource_type="user",
            resource_id=str(user.id),
        )

        return user

    def update_user(
        self,
        actor: User,
        target: User,
        username: str | None = None,
        is_active: bool | None = None,
        storage_quota_bytes: int | None = None,
        quota_updated: bool = False,
    ) -> User:

        if (
            username is not None
            and username != target.username
        ):

            existing = (
                self.users.get_by_username(
                    username
                )
            )

            if (
                existing
                and existing.id != target.id
            ):
                raise UserAlreadyExistsError(
                    "Username already exists"
                )

            target.username = username

        if is_active is not None:
            target.is_active = is_active

            if is_active:
                target.failed_login_attempts = 0
                target.locked_until = None

        if quota_updated:
            target.storage_quota_bytes = (
                storage_quota_bytes
            )

        self.users.update(target)

        self.audit_service.log(
            actor.id,
            ADMIN_USER_UPDATED,
            (
                f"updated user={target.id} "
                f"active={target.is_active} "
                f"quota={target.storage_quota_bytes}"
            ),
            resource_type="user",
            resource_id=str(target.id),
        )

        return target

    def set_roles(
        self,
        actor: User,
        target: User,
        role_names: list[str],
    ) -> User:

        self._assign_roles(
            target,
            role_names,
        )

        self.audit_service.log(
            actor.id,
            ADMIN_ROLE_ASSIGNED,
            (
                f"roles={','.join(role_names)} "
                f"user={target.id}"
            ),
            resource_type="user",
            resource_id=str(target.id),
        )

        return target

    def delete_user(
        self,
        actor: User,
        target: User,
    ) -> None:
        """
        Deactivate the account and revoke all of its
        sessions and refresh tokens. Records are kept
        for auditability.
        """

        target.is_active = False

        target.failed_login_attempts = 0

        self.users.update(target)

        self.refresh.revoke_all_for_user(
            target.id
        )

        for session in (
            self.sessions.list_for_user(
                target.id,
                include_revoked=True,
            )
        ):
            session.revoked = True
            self.sessions.update(session)

        self.audit_service.log(
            actor.id,
            ADMIN_USER_DELETED,
            (
                f"deactivated user={target.id} "
                f"email={target.email}"
            ),
            resource_type="user",
            resource_id=str(target.id),
        )

    # -------------------------------------------------

    def _assign_roles(
        self,
        user: User,
        role_names: list[str],
    ) -> None:

        if role_names:

            from app.domain.models.user_role import (
                UserRole,
            )

            existing_role_ids = {
                ur.role_id
                for ur in user.roles
            }

            roles = []

            for name in role_names:

                role = (
                    self.roles.get_by_name(name)
                )

                if not role:
                    raise NotFoundError(
                        f"Role '{name}' not found"
                    )

                if role.id in existing_role_ids:
                    continue

                roles.append(role)

            for role in roles:

                user.roles.append(
                    UserRole(role=role)
                )

        else:

            user.roles.clear()

        self.users.update(user)
