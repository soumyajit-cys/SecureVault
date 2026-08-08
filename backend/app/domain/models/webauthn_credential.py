from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.domain.models.base import BaseModel


class WebAuthnCredential(BaseModel):
    __tablename__ = "webauthn_credentials"

    # Base64url-encoded credential ID from the
    # authenticator.
    credential_id: Mapped[str] = mapped_column(
        String(512),
        unique=True,
        nullable=False,
        index=True,
    )

    # Base64url-encoded COSE public key.
    public_key: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Authenticator counter; a decrease implies a
    # cloned authenticator.
    sign_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    device_label: Mapped[str] = mapped_column(
        String(200),
        default="Security key",
        nullable=False,
    )

    aaguid: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
    )

    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user_id = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    user = relationship(
        "User",
        back_populates="webauthn_credentials",
    )
