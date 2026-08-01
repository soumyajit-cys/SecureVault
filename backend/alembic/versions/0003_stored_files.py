"""stored files

Revision ID: 0003_stored_files
Revises: 0002_crypto_keys
Create Date: 2026-08-02
"""

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects.postgresql import UUID

revision = "0003_stored_files"
down_revision = "0002_crypto_keys"
branch_labels = None
depends_on = None


def upgrade():

    op.create_table(
        "stored_files",
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
            "key_id",
            UUID(as_uuid=True),
            sa.ForeignKey(
                "crypto_keys.id",
                ondelete="SET NULL",
            ),
            nullable=True,
        ),
        sa.Column(
            "original_filename",
            sa.String(255),
            nullable=False,
        ),
        sa.Column(
            "storage_path",
            sa.String(500),
            nullable=False,
        ),
        sa.Column(
            "mime_type",
            sa.String(255),
            nullable=False,
            server_default="application/octet-stream",
        ),
        sa.Column(
            "original_size",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "encrypted_size",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "sha256",
            sa.String(64),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "is_folder",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "folder_file_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "deleted_at",
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
        "ix_stored_files_user_id",
        "stored_files",
        ["user_id"],
    )

    op.create_index(
        "ix_stored_files_key_id",
        "stored_files",
        ["key_id"],
    )

    op.create_index(
        "ix_stored_files_storage_path",
        "stored_files",
        ["storage_path"],
        unique=True,
    )

    op.create_index(
        "ix_stored_files_status",
        "stored_files",
        ["status"],
    )

    op.create_index(
        "ix_stored_files_is_folder",
        "stored_files",
        ["is_folder"],
    )


def downgrade():

    op.drop_index(
        "ix_stored_files_is_folder",
        table_name="stored_files",
    )

    op.drop_index(
        "ix_stored_files_status",
        table_name="stored_files",
    )

    op.drop_index(
        "ix_stored_files_storage_path",
        table_name="stored_files",
    )

    op.drop_index(
        "ix_stored_files_key_id",
        table_name="stored_files",
    )

    op.drop_index(
        "ix_stored_files_user_id",
        table_name="stored_files",
    )

    op.drop_table("stored_files")
