from datetime import timedelta

from app.core.config import get_settings
from app.schemas.token_claims import TokenClaims
from app.services.auth.jwt_key_service import (
    JwtKeyService,
)

settings = get_settings()


class JWTService:

    def __init__(
        self,
        key_service: JwtKeyService,
    ):
        self.key_service = key_service

    def create_token(
        self,
        claims: dict,
        expires_delta: timedelta,
    ) -> str:

        return (
            self.key_service
            .sign(
                claims,
                expires_delta,
            )
        )

    def decode_token(
        self,
        token: str,
    ) -> TokenClaims:

        payload = (
            self.key_service
            .decode(token)
        )

        return TokenClaims(
            **payload
        )