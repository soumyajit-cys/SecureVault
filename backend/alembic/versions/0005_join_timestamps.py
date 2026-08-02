"""add timestamps to user_roles and role_permissions

Revision ID: 0005_join_timestamps
Revises: 0004_refresh_token_rotation
Create Date: 2026-08-02
"""

from alembic import op
import sqlalchemy as sa

revision = "0005_join_timestamps"
down_revision = "0004_refresh_token_rotation"
branch_labels = None
depends_on = None


def upgrade():

    for table in ("user_roles", "role_permissions"):

        op.add_column(
            table,
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )

        op.add_column(
            table,
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )


def downgrade():

    for table in ("role_permissions", "user_roles"):

        op.drop_column(
            table,
            "updated_at",
        )

        op.drop_column(
            table,
            "created_at",
        )