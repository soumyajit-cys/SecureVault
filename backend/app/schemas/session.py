from datetime import datetime

from app.schemas.common import TimestampSchema


class SessionResponse(TimestampSchema):
    ip_address: str | None = None
    user_agent: str | None = None
    expires_at: datetime