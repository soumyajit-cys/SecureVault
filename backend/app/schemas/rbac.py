from pydantic import BaseModel


class PermissionInfo(
    BaseModel
):
    id: str
    name: str


class RoleInfo(
    BaseModel
):
    id: str
    name: str