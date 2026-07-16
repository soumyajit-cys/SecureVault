from app.services.auth.password_service import (
    Argon2PasswordService,
)

from app.services.auth.refresh_token_service import (
    RefreshTokenService,
)

from app.infrastructure.repositories.refresh_token_repository import (
    SQLAlchemyRefreshTokenRepository,
)

def get_password_service():
    return Argon2PasswordService()

def get_refresh_token_service(
    repository: SQLAlchemyRefreshTokenRepository,
):

    return RefreshTokenService(
        repository
    )