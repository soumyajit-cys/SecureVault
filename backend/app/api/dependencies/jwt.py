from app.services.auth.jwt_service import (
    JWTService,
)

from app.services.auth.token_service import (
    TokenService,
)


def get_jwt_service():
    return JWTService()


def get_token_service():
    return TokenService()