"""master data batch issues

Revision ID: d9f1a6b3c2e4
Revises: c7a2d4f9e8b1
Create Date: 2026-05-19 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "d9f1a6b3c2e4"
down_revision: str | None = "c7a2d4f9e8b1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "master_data_batches",
        sa.Column("issues_json", sa.Text(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_column("master_data_batches", "issues_json")
