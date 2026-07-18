from fastapi import Depends
from fastapi import HTTPException

from app.api.dependencies.current_user import (
    get_current_user,
)


def require_permission(
    permission_name: str,
):

    def checker(
        current_user=Depends(
            get_current_user
        ),
    ):

        permissions = []

        for user_role in current_user.roles:

            for rp in (
                user_role.role.permissions
            ):
                permissions.append(
                    rp.permission.name
                )

        if (
            permission_name
            not in permissions
        ):
            raise HTTPException(
                status_code=403,
                detail="Permission denied",
            )

        return current_user

    return checker