from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.domain.models.base import BaseModel


class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    action: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    resource_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    resource_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Hash-chaining: every entry carries the digest
    # of the entry that precedes it, so any in-place
    # edit breaks the chain and is detectable.
    # The first entry uses GENESIS_PREV_HASH.
    prev_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        server_default="0" * 64,
    )

    entry_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        server_default="0" * 64,
        index=True,
    )

    user_id = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    user = relationship(
        "User",
        back_populates="audit_logs",
    )

    