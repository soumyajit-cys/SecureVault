"""jwt signing keys at rest encryption

Revision ID: 0008_jwt_key_at_rest
Revises: 0007_jwt_signing_keys
Create Date: 2026-08-05
"""

from alembic import op
import sqlalchemy as sa

revision = "0008_jwt_key_at_rest"
down_revision = "0007_jwt_signing_keys"
branch_labels = None
depends_on = None


def upgrade():

    op.alter_column(
        "jwt_signing_keys",
        "private_key_pem",
        existing_type=sa.Text(),
        nullable=True,
    )

    op.add_column(
        "jwt_signing_keys",
        sa.Column(
            "encrypted_private_key_pem",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "jwt_signing_keys",
        sa.Column(
            "private_key_nonce",
            sa.String(128),
            nullable=True,
        ),
    )

    op.add_column(
        "jwt_signing_keys",
        sa.Column(
            "private_key_tag",
            sa.String(128),
            nullable=True,
        ),
    )

    op.add_column(
        "jwt_signing_keys",
        sa.Column(
            "private_key_salt",
            sa.String(128),
            nullable=True,
        ),
    )


def downgrade():

    op.drop_column(
        "jwt_signing_keys",
        "private_key_salt",
    )

    op.drop_column(
        "jwt_signing_keys",
        "private_key_tag",
    )

    op.drop_column(
        "jwt_signing_keys",
        "private_key_nonce",
    )

    op.drop_column(
        "jwt_signing_keys",
        "encrypted_private_key_pem",
    )

    op.alter_column(
        "jwt_signing_keys",
        "private_key_pem",
        existing_type=sa.Text(),
        nullable=False,
    )
