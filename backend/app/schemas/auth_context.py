from uuid import UUID

from pydantic import BaseModel


class AuthContext(
    BaseModel
):
    user_id: UUID

    email: str

    session_id: str

    roles: list[str]

    permissions: list[str]



    