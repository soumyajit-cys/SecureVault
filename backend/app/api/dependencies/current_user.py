from fastapi import Depends
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer

from app.api.dependencies.jwt import (
    get_jwt_service,
)

from app.api.dependencies.repositories import (
    get_user_repository,
)

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
    jwt_service=Depends(
        get_jwt_service
    ),
    user_repository=Depends(
        get_user_repository
    ),
):

    from uuid import UUID

    claims = jwt_service.decode_token(
        credentials.credentials
    )

    try:

        user_id = UUID(
            claims.sub
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=401,
            detail="Invalid subject identifier",
        ) from exc

    user = (
        user_repository.get(
            user_id
        )
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    return user