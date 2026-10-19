"""add owner_oid to jobs

Existing jobs are backfilled with the owner of their dataset: the job was started on that dataset, and the
dataset's owner is the best record we have of who that was. New jobs record the user who started them.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-19 09:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("owner_oid", sa.String(length=64), nullable=True))
    op.execute(
        "UPDATE jobs SET owner_oid = (SELECT owner_oid FROM datasets WHERE datasets.id = jobs.dataset_id)"
    )
    with op.batch_alter_table("jobs") as batch:  # batch mode: SQLite cannot alter a column in place
        batch.alter_column("owner_oid", existing_type=sa.String(length=64), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("jobs") as batch:
        batch.drop_column("owner_oid")
