"""file shares for multi-user sharing

Revision ID: 8a1f2c3d4e5f
Revises: 5c0705199c28
Create Date: 2026-09-17

Per-grant wrapped session keys: the container payload is never
re-encrypted; each grant stores RSA-4096-OAEP(session_key) under
the grantee's public key with per-grant revocation.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "8a1f2c3d4e5f"
down_revision: Union[str, Sequence[str], None] = "5c0705199c28"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "file_shares",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "file_id",
            UUID(as_uuid=True),
            sa.ForeignKey(
                "stored_files.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "owner_id",
            UUID(as_uuid=True),
            sa.ForeignKey(
                "users.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "grantee_id",
            UUID(as_uuid=True),
            sa.ForeignKey(
                "users.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "grantee_key_id",
            UUID(as_uuid=True),
            sa.ForeignKey(
                "crypto_keys.id",
                ondelete="SET NULL",
            ),
            nullable=True,
        ),
        sa.Column(
            "wrapped_key",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "key_algorithm",
            sa.String(50),
            nullable=False,
            server_default="RSA-4096-OAEP",
        ),
        sa.Column(
            "revoked_at",
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
        "ix_file_shares_file_id",
        "file_shares",
        ["file_id"],
    )

    op.create_index(
        "ix_file_shares_owner_id",
        "file_shares",
        ["owner_id"],
    )

    op.create_index(
        "ix_file_shares_grantee_id",
        "file_shares",
        ["grantee_id"],
    )

    op.create_index(
        "ix_file_shares_grantee_key_id",
        "file_shares",
        ["grantee_key_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_file_shares_grantee_key_id",
        table_name="file_shares",
    )

    op.drop_index(
        "ix_file_shares_grantee_id",
        table_name="file_shares",
    )

    op.drop_index(
        "ix_file_shares_owner_id",
        table_name="file_shares",
    )

    op.drop_index(
        "ix_file_shares_file_id",
        table_name="file_shares",
    )

    op.drop_table("file_shares")
