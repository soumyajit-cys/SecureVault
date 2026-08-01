from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.domain.models.base import BaseModel


class StoredFile(BaseModel):
    """
    Metadata record for an encrypted file stored on disk.

    The encrypted bytes live in the secure storage layout; this
    model only tracks the container path and its metadata.  The
    storage path is always a relative path generated from UUIDs,
    never derived from user input.
    """

    __tablename__ = "stored_files"

    user_id = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    key_id = mapped_column(
        ForeignKey("crypto_keys.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    storage_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        unique=True,
    )

    mime_type: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="application/octet-stream",
    )

    original_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )

    encrypted_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )

    sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="",
    )

    is_folder: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    folder_file_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        index=True,
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    @property
    def is_deleted(self) -> bool:
        return self.status == "deleted"
