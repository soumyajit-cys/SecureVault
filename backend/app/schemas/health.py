from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str = "1.0.0"
    environment: str = "development"


class ReadinessCheck(BaseModel):
    name: str
    status: Literal["ok", "degraded", "down"]
    detail: str = ""


class ReadinessResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    checks: list[ReadinessCheck]
    checked_at: datetime