from fastapi import Depends
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer

from app.api.dependencies.repositories import (
    get_user_repository,
)

from app.services.auth.jwt_service import (
    JWTService,
)

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
    user_repository=Depends(
        get_user_repository
    ),
):

    jwt_service = JWTService()

    claims = jwt_service.decode_token(
        credentials.credentials
    )

    user = (
        user_repository.get(
            claims.sub
        )
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    return user