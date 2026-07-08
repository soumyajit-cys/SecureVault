from datetime import datetime

from pydantic import BaseModel


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    expires_at: datetime
    revoked: bool


    