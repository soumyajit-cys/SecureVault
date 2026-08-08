from fastapi import Depends
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from starlette.requests import Request

from app.api.dependencies.jwt import (
    get_jwt_service,
)

from app.api.dependencies.repositories import (
    get_user_repository,
)

security = HTTPBearer(auto_error=False)


def get_current_session_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        security
    ),
    jwt_service=Depends(
        get_jwt_service
    ),
) -> str | None:
    """
    Session identifier embedded in the access token.
    Used by endpoints that must keep the calling
    session alive while revoking others.
    """

    if (
        credentials is None
        or not credentials.credentials
    ):
        return None

    claims = jwt_service.decode_token(
        credentials.credentials
    )

    return getattr(
        claims,
        "session_id",
        None,
    ) or None


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(
        security
    ),
    jwt_service=Depends(
        get_jwt_service
    ),
    user_repository=Depends(
        get_user_repository
    ),
):

    if (
        credentials is None
        or not credentials.credentials
    ):
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

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

    from app.core.request_context import (
        bind_actor,
    )

    bind_actor(
        user_id=user.id,
        session_id=getattr(
            claims,
            "session_id",
            None,
        ),
        request=request,
    )

    return user
