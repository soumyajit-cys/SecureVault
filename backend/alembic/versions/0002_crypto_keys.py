"""crypto keys

Revision ID: 0002_crypto_keys
Revises: 0001_identity_foundation
Create Date: 2026-08-02
"""

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects.postgresql import UUID

revision = "0002_crypto_keys"
down_revision = "0001_identity_foundation"
branch_labels = None
depends_on = None


def upgrade():

    op.create_table(
        "crypto_keys",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey(
                "users.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(100),
            nullable=False,
        ),
        sa.Column(
            "algorithm",
            sa.String(50),
            nullable=False,
            server_default="RSA-4096",
        ),
        sa.Column(
            "key_size",
            sa.Integer(),
            nullable=False,
            server_default="4096",
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "public_key_pem",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "encrypted_private_key_pem",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "private_key_nonce",
            sa.String(64),
            nullable=False,
        ),
        sa.Column(
            "private_key_tag",
            sa.String(64),
            nullable=False,
        ),
        sa.Column(
            "private_key_salt",
            sa.String(64),
            nullable=False,
        ),
        sa.Column(
            "fingerprint",
            sa.String(64),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "replaced_by_key_id",
            UUID(as_uuid=True),
            sa.ForeignKey(
                "crypto_keys.id",
                ondelete="SET NULL",
            ),
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
        "ix_crypto_keys_user_id",
        "crypto_keys",
        ["user_id"],
    )

    op.create_index(
        "ix_crypto_keys_fingerprint",
        "crypto_keys",
        ["fingerprint"],
        unique=True,
    )

    op.create_index(
        "ix_crypto_keys_status",
        "crypto_keys",
        ["status"],
    )

    op.create_index(
        "ix_crypto_keys_expires_at",
        "crypto_keys",
        ["expires_at"],
    )


def downgrade():

    op.drop_index(
        "ix_crypto_keys_expires_at",
        table_name="crypto_keys",
    )

    op.drop_index(
        "ix_crypto_keys_status",
        table_name="crypto_keys",
    )

    op.drop_index(
        "ix_crypto_keys_fingerprint",
        table_name="crypto_keys",
    )

    op.drop_index(
        "ix_crypto_keys_user_id",
        table_name="crypto_keys",
    )

    op.drop_table("crypto_keys")
