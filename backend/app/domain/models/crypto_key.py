from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.domain.models.base import BaseModel


class CryptoKey(BaseModel):
    """
    RSA encryption key owned by a user.

    The private key is stored encrypted at rest using AES-256-GCM
    with a key derived from the application secret, so a database
    leak alone does not expose private key material.
    """

    __tablename__ = "crypto_keys"

    user_id = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    algorithm: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="RSA-4096",
    )

    key_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=4096,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        index=True,
    )

    public_key_pem: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    encrypted_private_key_pem: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    private_key_nonce: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    private_key_tag: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    private_key_salt: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    fingerprint: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    replaced_by_key_id = mapped_column(
        ForeignKey(
            "crypto_keys.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    @property
    def is_revoked(self) -> bool:
        return self.status == "revoked"

    @property
    def is_expired(self) -> bool:
        return self.status == "expired"
