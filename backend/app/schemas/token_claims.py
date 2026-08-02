from datetime import datetime

from pydantic import BaseModel


class TokenClaims(
    BaseModel
):
    sub: str

    email: str

    session_id: str

    token_type: str

    jti: str | None = None

    exp: datetime