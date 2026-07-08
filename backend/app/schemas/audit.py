from app.schemas.common import TimestampSchema


class AuditLogResponse(TimestampSchema):
    action: str
    resource_type: str | None = None
    resource_id: str | None = None
    details: str | None = None

    