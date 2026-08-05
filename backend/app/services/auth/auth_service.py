from datetime import UTC
from datetime import datetime
from datetime import timedelta
from uuid import UUID

from app.services.auth.token_utils import (
    hash_token,
)

from app.core.config import get_settings
from app.core.exceptions import (
    AccountLockedError,
    InvalidCredentialsError,
    InvalidTokenError,
    MfaRequiredError,
    NotFoundError,
    UserAlreadyExistsError,
)

from app.domain.constants.audit_events import (
    PASSWORD_CHANGED,
    SESSION_REVOKED,
    SESSION_REVOKED_ALL,
    USER_LOGIN,
    USER_LOGOUT,
    USER_REGISTERED,
)

from app.domain.constants.auth import (
    DEFAULT_ROLE,
)

from app.domain.constants.token_types import (
    MFA_CHALLENGE,
)

from app.domain.models.session import Session

from app.schemas.auth_context import (
    AuthContext,
)

from app.services.audit_service import (
    AuditService,
)

from app.services.auth.login_rate_limiter import (
    LoginRateLimiter,
)

from app.services.auth.password_service import (
    Argon2PasswordService,
)

from app.services.auth.password_policy import (
    PasswordPolicy,
)

from app.services.auth.pwned_service import (
    PwnedPasswordChecker,
)

from app.services.auth.refresh_token_service import (
    RefreshTokenService,
)

from app.services.auth.session_service import (
    SessionService,
)

from app.services.auth.token_service import (
    TokenService,
)

settings = get_settings()


class AuthService:

    def __init__(
        self,
        user_repository,
        role_repository,
        session_repository,
        refresh_repository,
        audit_repository,
        jwt_service,
        mfa_service=None,
    ):
        self.users = user_repository
        self.roles = role_repository
        self.sessions = session_repository

        self.mfa_service = mfa_service

        self.password_service = (
            Argon2PasswordService()
        )

        self.token_service = (
            TokenService(
                jwt_service
            )
        )

        self.session_service = (
            SessionService(
                session_repository
            )
        )

        self.refresh_service = (
            RefreshTokenService(
                refresh_repository,
                jwt_service,
            )
        )

        self.audit_service = (
            AuditService(
                audit_repository
            )
        )

        self.rate_limiter = (
            LoginRateLimiter()
        )

        self.pwned = (
            PwnedPasswordChecker()
        )

    # -------------------------------------------------
    # Registration & password changes
    # -------------------------------------------------

    def register(
        self,
        email: str,
        username: str,
        password: str,
    ):

        self._validate_new_password(
            password
        )

        if self.users.get_by_email(
            email
        ):
            raise UserAlreadyExistsError(
                "Email already exists"
            )

        if self.users.get_by_username(
            username
        ):
            raise UserAlreadyExistsError(
                "Username already exists"
            )

        from app.domain.models.user import (
            User
        )

        user = User(
            email=email,
            username=username,
            password_hash=(
                self.password_service
                .hash_password(
                    password
                )
            ),
        )

        self.users.create(user)

        role = (
            self.roles.get_by_name(
                DEFAULT_ROLE
            )
        )

        if role:

            from app.domain.models.user_role import (
                UserRole,
            )

            user.roles.append(
                UserRole(role=role)
            )

        self.users.update(user)

        self.audit_service.log(
            user.id,
            USER_REGISTERED,
        )

        return user

    def change_password(
        self,
        user,
        current_password: str,
        new_password: str,
    ):

        if not (
            self.password_service
            .verify_password(
                current_password,
                user.password_hash,
            )
        ):
            raise InvalidCredentialsError(
                "Current password is incorrect"
            )

        self._validate_new_password(
            new_password
        )

        user.password_hash = (
            self.password_service
            .hash_password(
                new_password
            )
        )

        self.users.update(user)

        self.audit_service.log(
            user.id,
            PASSWORD_CHANGED,
        )

        return True

    # -------------------------------------------------
    # Login (password step + MFA step)
    # -------------------------------------------------

    def login(
        self,
        email: str,
        password: str,
        client_ip: str | None = None,
    ):

        self.rate_limiter.check(
            LoginRateLimiter.key(
                client_ip,
                email,
            )
        )

        user = (
            self.users.get_by_email(
                email
            )
        )

        if not user:
            raise InvalidCredentialsError()

        if not user.is_active:
            raise InvalidCredentialsError(
                "Account is deactivated"
            )

        if (
            user.locked_until
            and user.locked_until
            > datetime.now(UTC)
        ):
            raise AccountLockedError()

        if not (
            self.password_service
            .verify_password(
                password,
                user.password_hash,
            )
        ):

            user.failed_login_attempts += 1

            if (
                user.failed_login_attempts
                >= settings.MAX_LOGIN_ATTEMPTS
            ):
                user.locked_until = (
                    datetime.now(UTC)
                    + timedelta(
                        minutes=settings.ACCOUNT_LOCK_MINUTES
                    )
                )

            self.users.update(
                user
            )

            raise InvalidCredentialsError()

        user.failed_login_attempts = 0

        self.users.update(user)

        if user.totp_enabled:

            context = AuthContext(
                user_id=user.id,
                email=user.email,
                session_id="",
                roles=[],
                permissions=[],
            )

            return {
                "mfa_required": True,
                "mfa_token": (
                    self.token_service
                    .create_mfa_challenge(
                        context
                    )
                ),
            }

        return self._issue_tokens(user)

    def complete_login_with_mfa(
        self,
        mfa_token: str,
        code: str,
        client_ip: str | None = None,
    ):

        claims = (
            self.token_service
            .jwt_service
            .decode_token(
                mfa_token
            )
        )

        if claims.token_type != MFA_CHALLENGE:
            raise InvalidTokenError(
                "Invalid MFA challenge"
            )

        user = (
            self.users.get(
                UUID(claims.sub)
            )
        )

        if not user or not user.totp_enabled:
            raise InvalidTokenError(
                "Invalid MFA challenge"
            )

        self.rate_limiter.check(
            LoginRateLimiter.key(
                client_ip,
                user.email,
            )
        )

        from app.services.auth.mfa_service import (
            MfaService,
        )

        if not MfaService(
            self.users,
            None,
            None,
        ).verify_login_code(
            user,
            code,
        ):

            user.failed_login_attempts += 1

            if (
                user.failed_login_attempts
                >= settings.MAX_LOGIN_ATTEMPTS
            ):
                user.locked_until = (
                    datetime.now(UTC)
                    + timedelta(
                        minutes=settings.ACCOUNT_LOCK_MINUTES
                    )
                )

            self.users.update(user)

            from app.domain.constants.audit_events import (
                MFA_VERIFY_FAILED,
            )

            self.audit_service.log(
                user.id,
                MFA_VERIFY_FAILED,
            )

            raise InvalidCredentialsError(
                "Invalid MFA code"
            )

        user.failed_login_attempts = 0

        self.users.update(user)

        return self._issue_tokens(user)

    def _issue_tokens(self, user):

        session_identifier = (
            self.session_service
            .create_session_identifier()
        )

        session = Session(
            session_identifier=session_identifier,
            expires_at=(
                datetime.now(UTC)
                + timedelta(
                    days=settings.REFRESH_TOKEN_EXPIRE_DAYS
                )
            ),
            last_seen_at=datetime.now(UTC),
            user_id=user.id,
        )

        self.sessions.create(
            session
        )

        context = AuthContext(
            user_id=user.id,
            email=user.email,
            session_id=session_identifier,
            roles=[],
            permissions=[],
        )

        access_token = (
            self.token_service
            .create_access_token(
                context
            )
        )

        refresh_token = (
            self.refresh_service
            .issue_initial_refresh_token(
                context,
                session.expires_at,
            )
        )

        self.audit_service.log(
            user.id,
            USER_LOGIN,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    # -------------------------------------------------
    # Logout / refresh
    # -------------------------------------------------

    def logout(
        self,
        refresh_token: str,
    ):

        claims = (
            self.refresh_service
            .jwt_service
            .decode_token(
                refresh_token
            )
        )

        token_hash = (
            hash_token(
                refresh_token
            )
        )

        token = (
            self.refresh_service
            .repository
            .get_by_token_hash(
                token_hash
            )
        )

        if token:

            self.refresh_service.repository.revoke_family(
                token.token_family
            )

        self.audit_service.log(
            claims.sub,
            USER_LOGOUT,
        )

        return True

    def refresh(self, refresh_token: str):

        claims = (
            self.refresh_service
            .jwt_service
            .decode_token(
                refresh_token
            )
        )

        user = self.users.get(
            claims.sub
        )

        context = AuthContext(
            user_id=user.id,
            email=user.email,
            session_id=claims.session_id,
            roles=[],
            permissions=[],
        )

        new_refresh = (
            self.refresh_service
            .rotate(
                refresh_token,
                context,
                datetime.now(UTC)
                + timedelta(
                    days=settings.REFRESH_TOKEN_EXPIRE_DAYS
                ),
            )
        )

        access = (
            self.token_service
            .create_access_token(
                context
            )
        )

        self._touch_session(
            claims.session_id
        )

        return {
            "access_token": access,
            "refresh_token": new_refresh,
        }

    def _touch_session(
        self,
        session_identifier: str,
    ):

        session = (
            self.sessions
            .get_active_by_identifier(
                session_identifier
            )
        )

        if session:
            self.sessions.mark_seen(
                session,
                datetime.now(UTC),
            )

    # -------------------------------------------------
    # Session management
    # -------------------------------------------------

    def list_sessions(
        self,
        user,
    ):

        return (
            self.sessions.list_for_user(
                user.id
            )
        )

    def revoke_session(
        self,
        user,
        session_id: UUID,
    ):

        session = (
            self.sessions.get_for_user(
                user.id,
                session_id,
            )
        )

        if not session:
            raise NotFoundError(
                "Session not found"
            )

        if session.revoked:
            raise NotFoundError(
                "Session not found"
            )

        session.revoked = True

        self.sessions.update(session)

        self.refresh_service.repository.revoke_by_session_id(
            session.session_identifier
        )

        self.audit_service.log(
            user.id,
            SESSION_REVOKED,
            (
                f"revoked session "
                f"session_id={session.id}"
            ),
            resource_type="session",
            resource_id=str(session.id),
        )

        return session

    def revoke_all_sessions(
        self,
        user,
        exclude_session_identifier: str | None = None,
    ):

        sessions = (
            self.sessions.list_for_user(
                user.id,
                include_revoked=True,
            )
        )

        revoked_count = 0

        for session in sessions:

            if (
                exclude_session_identifier
                and session.session_identifier
                == exclude_session_identifier
            ):
                continue

            if session.revoked:
                continue

            session.revoked = True

            self.sessions.update(session)

            self.refresh_service.repository.revoke_by_session_id(
                session.session_identifier
            )

            revoked_count += 1

        self.audit_service.log(
            user.id,
            SESSION_REVOKED_ALL,
            f"revoked {revoked_count} sessions",
        )

        return revoked_count

    # -------------------------------------------------
    # Password validation helpers
    # -------------------------------------------------

    def _validate_new_password(
        self,
        password: str,
    ):

        result = PasswordPolicy.validate(
            password
        )

        if not result.valid:

            from app.core.exceptions import (
                WeakPasswordError,
            )

            raise WeakPasswordError(
                result.message
            )

        self.pwned.assert_not_pwned(
            password
        )
