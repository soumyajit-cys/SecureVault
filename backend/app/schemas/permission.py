from app.schemas.common import TimestampSchema


class PermissionBase(TimestampSchema):
    name: str
    description: str | None = None


class PermissionResponse(PermissionBase):
    pass


