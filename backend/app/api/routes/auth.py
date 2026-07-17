from fastapi import APIRouter
from fastapi import Depends

from app.api.dependencies.auth import (
    get_auth_service,
)

from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/register")
def register(
    payload: RegisterRequest,
    auth_service=Depends(
        get_auth_service
    ),
):
    return auth_service.register(
        payload.email,
        payload.username,
        payload.password,
    )


@router.post("/login")
def login(
    payload: LoginRequest,
    auth_service=Depends(
        get_auth_service
    ),
):
    return auth_service.login(
        payload.email,
        payload.password,
    )