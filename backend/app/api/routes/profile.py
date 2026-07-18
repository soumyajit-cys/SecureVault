from fastapi import APIRouter
from fastapi import Depends

from app.api.dependencies.current_user import (
    get_current_user,
)

router = APIRouter(
    prefix="/profile",
    tags=["Profile"],
)


@router.get("/me")
def me(
    current_user=Depends(
        get_current_user
    ),
):
    return {
        "id": str(
            current_user.id
        ),
        "email": current_user.email,
        "username": current_user.username,
    }