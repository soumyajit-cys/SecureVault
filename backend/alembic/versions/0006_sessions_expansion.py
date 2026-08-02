"""add session identifier, device name and revoked columns

Revision ID: 0006_sessions_expansion
Revises: 0005_join_timestamps
Create Date: 2026-08-02
"""

from alembic import op
import sqlalchemy as sa

revision = "0006_sessions_expansion"
down_revision = "0005_join_timestamps"
branch_labels = None
depends_on = None


def upgrade():

    op.add_column(
        "sessions",
        sa.Column(
            "session_identifier",
            sa.String(255),
            nullable=False,
            server_default="",
        ),
    )

    op.add_column(
        "sessions",
        sa.Column(
            "device_name",
            sa.String(255),
            nullable=True,
        ),
    )

    op.add_column(
        "sessions",
        sa.Column(
            "revoked",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.create_index(
        "ix_sessions_session_identifier",
        "sessions",
        ["session_identifier"],
        unique=True,
    )


def downgrade():

    op.drop_index(
        "ix_sessions_session_identifier",
        table_name="sessions",
    )

    op.drop_column(
        "sessions",
        "revoked",
    )

    op.drop_column(
        "sessions",
        "device_name",
    )

    op.drop_column(
        "sessions",
        "session_identifier",
    )