from datetime import UTC
from datetime import datetime
from datetime import timedelta

import jwt

from app.core.config import get_settings
from app.core.exceptions import InvalidTokenError
from app.core.exceptions import TokenExpiredError
from app.schemas.token_claims import TokenClaims

settings = get_settings()


class JWTService:

    def create_token(
        self,
        claims: dict,
        expires_delta: timedelta,
    ) -> str:

        payload = claims.copy()

        payload["exp"] = (
            datetime.now(UTC)
            + expires_delta
        )

        return jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

    def decode_token(
        self,
        token: str,
    ) -> TokenClaims:

        try:

            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[
                    settings.JWT_ALGORITHM
                ],
            )

            return TokenClaims(
                **payload
            )

        except jwt.ExpiredSignatureError:
            raise TokenExpiredError(
                "Token expired"
            )

        except jwt.InvalidTokenError:
            raise InvalidTokenError(
                "Invalid token"
            )