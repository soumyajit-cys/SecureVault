from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict


class ORMBaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )


class UUIDSchema(ORMBaseSchema):
    id: UUID


class TimestampSchema(UUIDSchema):
    created_at: datetime
    updated_at: datetime