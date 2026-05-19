"""master data template sheets

Revision ID: b8e4f2a9c1d6
Revises: b1d9c3e7a5f0
Create Date: 2026-05-19 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "b8e4f2a9c1d6"
down_revision: str | None = "b1d9c3e7a5f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "master_data_templates",
        sa.Column("sheets_json", sa.Text(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_column("master_data_templates", "sheets_json")
