from fastapi import APIRouter
from fastapi import Depends

from app.api.dependencies.rbac import (
    require_role,
)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


@router.get("/status")
def admin_status(
    user=Depends(
        require_role(
            "Admin"
        )
    ),
):
    return {
        "status": "ok"
    }