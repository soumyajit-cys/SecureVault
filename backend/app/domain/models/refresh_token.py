from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.domain.models.base import BaseModel


class RefreshToken(BaseModel):
    __tablename__ = "refresh_tokens"

    token_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    user_id = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="refresh_tokens",
    )