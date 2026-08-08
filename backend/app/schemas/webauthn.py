from pydantic import BaseModel
from pydantic import Field


class PasskeyRegistrationBeginResponse(BaseModel):
    options: dict


class PasskeyRegistrationCompleteRequest(BaseModel):
    response: dict
    device_label: str = Field(
        default="Security key",
        max_length=200,
    )


class PasskeyCredentialResponse(BaseModel):
    id: str
    device_label: str
    created_at: str | None = None
    last_used_at: str | None = None


class PasskeyLoginBeginRequest(BaseModel):
    email: str | None = Field(
        default=None,
        max_length=255,
    )


class PasskeyLoginBeginResponse(BaseModel):
    options: dict


class PasskeyLoginCompleteRequest(BaseModel):
    response: dict


class MfaPolicyResponse(BaseModel):
    mode: str
    users_with_mfa: int
    total_users: int
    default_mode: str


class MfaPolicyUpdateRequest(BaseModel):
    mode: str = Field(
        pattern="^(optional|required)$"
    )
