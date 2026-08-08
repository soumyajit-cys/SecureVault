from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.core.database import Base
from app.domain.models.base import TimestampMixin


class AppSetting(Base, TimestampMixin):
    """
    Server-wide runtime policy flags (key/value).

    Used for the MFA enforcement policy so admins
    can toggle it without redeploying.
    """

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    value: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
