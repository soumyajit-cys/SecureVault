"""search upgrades trigram

Revision ID: 5c0705199c28
Revises: 4c6d246c56dd
Create Date: 2026-08-08 14:11:58.970718

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c0705199c28'
down_revision: Union[str, Sequence[str], None] = '4c6d246c56dd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Fuzzy-substring search on file names: the GIN
    # trigram index serves ILIKE '%...%' patterns on
    # Postgres.
    op.execute(
        "CREATE EXTENSION IF NOT EXISTS pg_trgm"
    )

    op.create_index(
        "ix_stored_files_original_filename_trgm",
        "stored_files",
        ["original_filename"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={
            "original_filename": "gin_trgm_ops"
        },
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        "ix_stored_files_original_filename_trgm",
        table_name="stored_files",
        postgresql_using="gin",
    )
