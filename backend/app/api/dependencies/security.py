from fastapi import Depends

from app.services.auth.password_service import (
    Argon2PasswordService,
)

from app.services.auth.refresh_token_service import (
    RefreshTokenService,
)

from app.infrastructure.repositories.refresh_token_repository import (
    SQLAlchemyRefreshTokenRepository,
)

from app.api.dependencies.jwt import (
    get_jwt_service,
)

def get_password_service():
    return Argon2PasswordService()


def get_refresh_token_service(
    repository: SQLAlchemyRefreshTokenRepository,
    jwt_service=Depends(
        get_jwt_service
    ),
):

    return RefreshTokenService(
        repository,
        jwt_service,
    )