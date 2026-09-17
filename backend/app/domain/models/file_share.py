from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.domain.models.base import BaseModel


class FileShare(BaseModel):
    """
    Per-grant wrapped session key for multi-user sharing.

    The file payload is never re-encrypted: the owner's AES session
    key is unwrapped with the owner's RSA private key and re-wrapped
    (RSA-4096-OAEP) under the grantee's active RSA public key. Each
    grantee therefore decrypts the same container independently with
    their own private key.

    Revocation sets ``revoked_at``; it blocks future downloads but
    does not rotate the session key, so a grantee who cached the
    plaintext (or the unwrapped session key) retains it. True
    cryptographic removal requires re-encrypting the file (future
    work) — see docs/security.md.
    """

    __tablename__ = "file_shares"

    file_id = mapped_column(
        ForeignKey("stored_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    owner_id = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    grantee_id = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    grantee_key_id = mapped_column(
        ForeignKey("crypto_keys.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Base64 RSA-OAEP(session_key) under the grantee public key.
    wrapped_key: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    key_algorithm: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="RSA-4096-OAEP",
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None
