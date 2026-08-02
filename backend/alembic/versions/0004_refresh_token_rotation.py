"""refresh token rotation fields

Revision ID: 0004_refresh_token_rotation
Revises: 0003_stored_files
Create Date: 2026-08-02
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_refresh_token_rotation"
down_revision = "0003_stored_files"
branch_labels = None
depends_on = None


def upgrade():

    op.add_column(
        "refresh_tokens",
        sa.Column(
            "token_family",
            sa.String(255),
            nullable=False,
            server_default="",
        ),
    )

    op.add_column(
        "refresh_tokens",
        sa.Column(
            "session_id",
            sa.String(255),
            nullable=False,
            server_default="",
        ),
    )

    op.add_column(
        "refresh_tokens",
        sa.Column(
            "replaced_by_token",
            sa.String(255),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_refresh_tokens_token_family",
        "refresh_tokens",
        ["token_family"],
    )

    op.create_index(
        "ix_refresh_tokens_session_id",
        "refresh_tokens",
        ["session_id"],
    )


def downgrade():

    op.drop_index(
        "ix_refresh_tokens_session_id",
        table_name="refresh_tokens",
    )

    op.drop_index(
        "ix_refresh_tokens_token_family",
        table_name="refresh_tokens",
    )

    op.drop_column(
        "refresh_tokens",
        "replaced_by_token",
    )

    op.drop_column(
        "refresh_tokens",
        "session_id",
    )

    op.drop_column(
        "refresh_tokens",
        "token_family",
    )