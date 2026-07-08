from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import EmailStr
from pydantic import Field

from app.schemas.audit import AuditLogResponse
from app.schemas.common import TimestampSchema
from app.schemas.role import RoleResponse
from app.schemas.session import SessionResponse


class UserCreate(BaseModel):
    email: EmailStr

    username: str = Field(
        min_length=3,
        max_length=100,
    )

    password: str = Field(
        min_length=12,
        max_length=128,
    )


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    username: str | None = None


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


class UserResponse(TimestampSchema):
    email: EmailStr
    username: str

    is_active: bool
    is_verified: bool

    failed_login_attempts: int

    locked_until: datetime | None = None

    roles: list[RoleResponse] = []


class UserProfile(UserResponse):
    sessions: list[SessionResponse] = []
    audit_logs: list[AuditLogResponse] = []

    model_config = ConfigDict(
        from_attributes=True
    )