from datetime import UTC
from datetime import datetime
from datetime import timedelta

from app.core.config import get_settings
from app.core.exceptions import (
    AccountLockedError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
)

from app.domain.constants.audit_events import (
    USER_LOGIN,
    USER_LOGOUT,
    USER_REGISTERED,
)

from app.domain.constants.auth import (
    DEFAULT_ROLE,
)

from app.domain.models.session import Session

from app.schemas.auth_context import (
    AuthContext,
)

from app.services.audit_service import (
    AuditService,
)

from app.services.auth.password_service import (
    Argon2PasswordService,
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
    ):
        self.users = user_repository
        self.roles = role_repository
        self.sessions = session_repository

        self.password_service = (
            Argon2PasswordService()
        )

        self.token_service = (
            TokenService()
        )

        self.session_service = (
            SessionService(
                session_repository
            )
        )

        self.refresh_service = (
            RefreshTokenService(
                refresh_repository
            )
        )

        self.audit_service = (
            AuditService(
                audit_repository
            )
        )

    def register(
        self,
        email: str,
        username: str,
        password: str,
    ):

        if self.users.get_by_email(
            email
        ):
            raise UserAlreadyExistsError(
                "Email already exists"
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
            user.roles.append(role)

        self.users.update(user)

        self.audit_service.log(
            user.id,
            USER_REGISTERED,
        )

        return user

    def login(
        self,
        email: str,
        password: str,
    ):

        user = (
            self.users.get_by_email(
                email
            )
        )

        if not user:
            raise InvalidCredentialsError()

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

    def logout(
        self,
        user_id,
    ):

        self.audit_service.log(
            user_id,
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

    return {
            
        "access_token": access,
        "refresh_token": new_refresh,
    }