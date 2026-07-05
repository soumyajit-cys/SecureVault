from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get(
    "",
    response_model=HealthResponse,
)
async def health_check():
    return HealthResponse(
        status="healthy",
        service="SecureVault",
    )


