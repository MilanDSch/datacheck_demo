"""add visibility to datasets

Every existing dataset becomes private, so the upgrade exposes nothing. Owners can publish later.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-19 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # server_default fills the existing rows; the model sets the value for new ones.
    op.add_column(
        "datasets",
        sa.Column("visibility", sa.String(length=20), nullable=False, server_default="private"),
    )


def downgrade() -> None:
    with op.batch_alter_table("datasets") as batch:
        batch.drop_column("visibility")
