from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import (
    PlainTextResponse,
)

from app.core.config import get_settings
from app.core.metrics import (
    render_metrics,
)

router = APIRouter(
    prefix="/metrics",
    tags=["Metrics"],
)


@router.get(
    "",
    response_class=PlainTextResponse,
    include_in_schema=False,
)
async def metrics_endpoint(
    request: Request,
):

    settings = get_settings()

    if not settings.ENABLE_METRICS:
        return PlainTextResponse(
            "Metrics disabled",
            status_code=404,
        )

    return PlainTextResponse(
        render_metrics(),
        headers={
            "Content-Type": (
                "text/plain; "
                "version=0.0.4"
            ),
        },
    )