from pydantic import BaseModel


class DerivedKey(
    BaseModel
):
    key: bytes

    salt: bytes