from app.schemas.common import TimestampSchema
from app.schemas.permission import PermissionResponse


class RoleBase(TimestampSchema):
    name: str
    description: str | None = None


class RoleResponse(RoleBase):
    permissions: list[PermissionResponse] = []