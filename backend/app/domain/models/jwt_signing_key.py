from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.domain.models.base import BaseModel


class JwtSigningKey(BaseModel):
    __tablename__ = "jwt_signing_keys"

    key_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    algorithm: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="RS256",
    )

    public_key_pem: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # At-rest envelope (base64 ciphertext/nonce/tag/salt) produced by
    # ``app.core.at_rest.encrypt_secret``. ``private_key_pem`` remains
    # for pre-encryption rows only and is NULL for new keys.
    private_key_pem: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    encrypted_private_key_pem: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    private_key_nonce: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    private_key_tag: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    private_key_salt: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    @property
    def has_encrypted_private_key(self) -> bool:
        return bool(self.encrypted_private_key_pem)

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        index=True,
    )

    retired_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )