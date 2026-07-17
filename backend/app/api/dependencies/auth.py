from fastapi import Depends

from app.api.dependencies.repositories import (
    get_audit_repository,
    get_refresh_token_repository,
    get_role_repository,
    get_session_repository,
    get_user_repository,
)

from app.services.auth.auth_service import (
    AuthService,
)


def get_auth_service(
    user_repository=Depends(
        get_user_repository
    ),
    role_repository=Depends(
        get_role_repository
    ),
    session_repository=Depends(
        get_session_repository
    ),
    refresh_repository=Depends(
        get_refresh_token_repository
    ),
    audit_repository=Depends(
        get_audit_repository
    ),
):

    return AuthService(
        user_repository,
        role_repository,
        session_repository,
        refresh_repository,
        audit_repository,
    )