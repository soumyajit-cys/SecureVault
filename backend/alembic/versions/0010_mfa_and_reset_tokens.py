"""mfa recovery codes and password reset tokens

Revision ID: 0010_mfa_and_reset_tokens
Revises: 0009_user_enterprise_fields
Create Date: 2026-08-05
"""

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects.postgresql import UUID

revision = "0010_mfa_and_reset_tokens"
down_revision = "0009_user_enterprise_fields"
branch_labels = None
depends_on = None


def _id_column():
    return sa.Column(
        "id",
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
    )


def _timestamps():

    return [
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
    ]


def upgrade():

    op.create_table(
        "password_reset_tokens",
        _id_column(),
        sa.Column(
            "token_hash",
            sa.String(64),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "used_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            nullable=False,
        ),
        *_timestamps(),
    )

    op.create_index(
        "ix_password_reset_tokens_token_hash",
        "password_reset_tokens",
        ["token_hash"],
        unique=True,
    )

    op.create_foreign_key(
        "fk_password_reset_tokens_user_id_users",
        "password_reset_tokens",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_table(
        "mfa_recovery_codes",
        _id_column(),
        sa.Column(
            "code_hash",
            sa.String(64),
            nullable=False,
        ),
        sa.Column(
            "used_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            nullable=False,
        ),
        *_timestamps(),
    )

    op.create_index(
        "ix_mfa_recovery_codes_code_hash",
        "mfa_recovery_codes",
        ["code_hash"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_mfa_recovery_codes_user_id_users",
        "mfa_recovery_codes",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade():

    op.drop_constraint(
        "fk_mfa_recovery_codes_user_id_users",
        "mfa_recovery_codes",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_mfa_recovery_codes_code_hash",
        table_name="mfa_recovery_codes",
    )

    op.drop_table("mfa_recovery_codes")

    op.drop_constraint(
        "fk_password_reset_tokens_user_id_users",
        "password_reset_tokens",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_password_reset_tokens_token_hash",
        table_name="password_reset_tokens",
    )

    op.drop_table("password_reset_tokens")
