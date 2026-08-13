from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import Field


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class MfaSetupRequest(BaseModel):
    pass


class MfaEnableRequest(BaseModel):
    secret: str
    code: str = Field(
        min_length=6,
        max_length=6,
    )


class MfaDisableRequest(BaseModel):
    code: str


class MfaVerifyRequest(BaseModel):
    mfa_token: str
    code: str = Field(
        min_length=6,
        max_length=24,
    )


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str


class EmailVerificationRequest(BaseModel):
    token: str = Field(
        min_length=8,
        max_length=128,
    )