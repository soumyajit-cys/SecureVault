from datetime import datetime

from pydantic import BaseModel


class KeyMetadata(
    BaseModel
):
    key_id: str

    algorithm: str

    created_at: datetime

    expires_at: datetime | None = None