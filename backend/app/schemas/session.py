from datetime import datetime

from app.schemas.common import (
    TimestampSchema
)


class SessionResponse(
    TimestampSchema
):
    session_identifier: str

    device_name: str | None = None

    ip_address: str | None = None

    user_agent: str | None = None

    revoked: bool

    expires_at: datetime


    