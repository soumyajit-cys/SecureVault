from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.domain.models.base import BaseModel


class MfaRecoveryCode(BaseModel):
    __tablename__ = "mfa_recovery_codes"

    # SHA-256 of the raw recovery code; high-entropy by design,
    # so a plain digest is sufficient.
    code_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user_id = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="mfa_recovery_codes",
    )
