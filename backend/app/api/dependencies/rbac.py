from fastapi import Depends
from fastapi import HTTPException

from app.api.dependencies.current_user import (
    get_current_user,
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