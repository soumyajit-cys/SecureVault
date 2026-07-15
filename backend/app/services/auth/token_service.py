from datetime import timedelta

from app.core.config import get_settings

from app.domain.constants.token_types import (
    ACCESS_TOKEN,
    REFRESH_TOKEN,
)

from app.schemas.auth_context import (
    AuthContext,
)

from app.services.auth.jwt_service import (
    JWTService,
)

settings = get_settings()


class TokenService:

    def __init__(self):

        self.jwt_service = (
            JWTService()
        )

    def create_access_token(
        self,
        context: AuthContext,
    ) -> str:

        claims = {
            "sub": str(
                context.user_id
            ),
            "email": context.email,
            "session_id": context.session_id,
            "token_type": ACCESS_TOKEN,
        }

        return (
            self.jwt_service.create_token(
                claims,
                timedelta(
                    minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
                ),
            )
        )

    def create_refresh_token(
        self,
        context: AuthContext,
    ) -> str:

        claims = {
            "sub": str(
                context.user_id
            ),
            "email": context.email,
            "session_id": context.session_id,
            "token_type": REFRESH_TOKEN,
        }

        return (
            self.jwt_service.create_token(
                claims,
                timedelta(
                    days=settings.REFRESH_TOKEN_EXPIRE_DAYS
                ),
            )
        )