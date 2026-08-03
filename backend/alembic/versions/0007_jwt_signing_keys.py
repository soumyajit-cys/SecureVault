"""jwt signing keys

Revision ID: 0007_jwt_signing_keys
Revises: 0006_sessions_expansion
Create Date: 2026-08-03
"""

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects.postgresql import UUID

revision = "0007_jwt_signing_keys"
down_revision = "0006_sessions_expansion"
branch_labels = None
depends_on = None


def upgrade():

    op.create_table(
        "jwt_signing_keys",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "key_id",
            sa.String(64),
            nullable=False,
        ),
        sa.Column(
            "algorithm",
            sa.String(10),
            nullable=False,
            server_default="RS256",
        ),
        sa.Column(
            "public_key_pem",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "private_key_pem",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "retired_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_jwt_signing_keys_key_id",
        "jwt_signing_keys",
        ["key_id"],
        unique=True,
    )

    op.create_index(
        "ix_jwt_signing_keys_status",
        "jwt_signing_keys",
        ["status"],
    )


def downgrade():

    op.drop_index(
        "ix_jwt_signing_keys_status",
        table_name="jwt_signing_keys",
    )

    op.drop_index(
        "ix_jwt_signing_keys_key_id",
        table_name="jwt_signing_keys",
    )

    op.drop_table("jwt_signing_keys")