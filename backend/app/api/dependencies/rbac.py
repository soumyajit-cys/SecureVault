from fastapi import Depends
from fastapi import HTTPException

from app.api.dependencies.auth import (
    get_webauthn_service,
)
from app.api.dependencies.current_user import (
    get_current_user,
)
from app.domain.constants.auth import (
    ADMIN_ROLE,
    AUDITOR_ROLE,
)


def require_role(
    role_name: str,
):

    def checker(
        current_user=Depends(
            get_current_user
        ),
    ):

        roles = [
            user_role.role.name
            for user_role
            in current_user.roles
        ]

        if role_name not in roles:

            raise HTTPException(
                status_code=403,
                detail="Forbidden",
            )

        return current_user

    return checker


def require_privileged_mfa(
    current_user=Depends(
        get_current_user
    ),
    webauthn_service=Depends(
        get_webauthn_service
    ),
):

    roles = [
        user_role.role.name
        for user_role
        in current_user.roles
    ]

    is_privileged = (
        (ADMIN_ROLE in roles)
        or (AUDITOR_ROLE in roles)
    )

    if not is_privileged:
        raise HTTPException(
            status_code=403,
            detail="Forbidden",
        )

    if not (
        webauthn_service
        .user_has_mfa(current_user)
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "MFA enrollment required for "
                "Admin/Auditor roles"
            ),
        )

    return current_user