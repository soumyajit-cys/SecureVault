from fastapi import Depends

from app.api.dependencies.repositories import (
    get_jwt_signing_key_repository,
)

from app.services.auth.jwt_key_service import (
    JwtKeyService,
)

from app.services.auth.jwt_service import (
    JWTService,
)

from app.services.auth.token_service import (
    TokenService,
)


def get_jwt_key_service(
    repository=Depends(
        get_jwt_signing_key_repository
    ),
):
    return JwtKeyService(
        repository
    )


def get_jwt_service(
    key_service=Depends(
        get_jwt_key_service
    ),
):
    return JWTService(
        key_service
    )


def get_token_service(
    jwt_service=Depends(
        get_jwt_service
    ),
):
    return TokenService(
        jwt_service
    )