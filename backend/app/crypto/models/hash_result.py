from pydantic import BaseModel


class HashResult(
    BaseModel
):
    algorithm: str

    digest: str