from datetime import datetime

from uuid import UUID

from app.schemas.common import (
    TimestampSchema
)


class SessionResponse(
    TimestampSchema
):
    id: UUID

    session_identifier: str

    device_name: str | None = None

    ip_address: str | None = None

    user_agent: str | None = None

    revoked: bool

    expires_at: datetime

    last_seen_at: datetime | None = None


    