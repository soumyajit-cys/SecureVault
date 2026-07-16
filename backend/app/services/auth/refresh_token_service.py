from datetime import UTC
from datetime import datetime

from app.core.exceptions import InvalidTokenError
from app.domain.constants.token_types import REFRESH_TOKEN
from app.domain.models.refresh_token import RefreshToken
from app.infrastructure.repositories.refresh_token_repository import (
    SQLAlchemyRefreshTokenRepository,
)
from app.schemas.auth_context import AuthContext
from app.services.auth.jwt_service import JWTService
from app.services.auth.token_service import TokenService
from app.services.auth.token_utils import (
    generate_token_family,
    hash_token,
)


class RefreshTokenService:

    def __init__(
        self,
        token_repository: SQLAlchemyRefreshTokenRepository,
    ):
        self.repository = token_repository
        self.jwt_service = JWTService()
        self.token_service = TokenService()

    def issue_initial_refresh_token(
        self,
        context: AuthContext,
        expires_at: datetime,
    ) -> str:

        token = (
            self.token_service
            .create_refresh_token(context)
        )

        self.repository.create(
            RefreshToken(
                token_hash=hash_token(token),
                token_family=generate_token_family(),
                session_id=context.session_id,
                expires_at=expires_at,
                user_id=context.user_id,
            )
        )

        return token

    def rotate(
        self,
        refresh_token: str,
        context: AuthContext,
        expires_at: datetime,
    ) -> str:

        claims = self.jwt_service.decode_token(
            refresh_token
        )

        if claims.token_type != REFRESH_TOKEN:
            raise InvalidTokenError(
                "Invalid refresh token"
            )

        token_hash = hash_token(
            refresh_token
        )

        stored = (
            self.repository
            .get_by_token_hash(
                token_hash
            )
        )

        if not stored:
            raise InvalidTokenError(
                "Refresh token not found"
            )

        if stored.revoked:
            self.repository.revoke_family(
                stored.token_family
            )

            raise InvalidTokenError(
                "Replay attack detected"
            )

        new_token = (
            self.token_service
            .create_refresh_token(
                context
            )
        )

        stored.revoked = True
        stored.replaced_by_token = (
            hash_token(new_token)
        )

        self.repository.update(
            stored
        )

        self.repository.create(
            RefreshToken(
                token_hash=hash_token(
                    new_token
                ),
                token_family=stored.token_family,
                session_id=context.session_id,
                expires_at=expires_at,
                user_id=context.user_id,
            )
        )

        return new_token