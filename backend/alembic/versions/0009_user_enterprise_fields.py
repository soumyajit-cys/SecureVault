"""enterprise user profile and session fields

Revision ID: 0009_user_enterprise_fields
Revises: 0008_jwt_key_at_rest
Create Date: 2026-08-05
"""

from alembic import op
import sqlalchemy as sa

revision = "0009_user_enterprise_fields"
down_revision = "0008_jwt_key_at_rest"
branch_labels = None
depends_on = None


def upgrade():

    op.add_column(
        "users",
        sa.Column(
            "totp_secret",
            sa.String(128),
            nullable=True,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "totp_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "totp_enabled_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "users",
        sa.Column(
            "storage_quota_bytes",
            sa.BigInteger(),
            nullable=True,
        ),
    )

    op.add_column(
        "sessions",
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade():

    op.drop_column(
        "sessions",
        "last_seen_at",
    )

    op.drop_column(
        "users",
        "storage_quota_bytes",
    )

    op.drop_column(
        "users",
        "totp_enabled_at",
    )

    op.drop_column(
        "users",
        "totp_enabled",
    )

    op.drop_column(
        "users",
        "totp_secret",
    )
