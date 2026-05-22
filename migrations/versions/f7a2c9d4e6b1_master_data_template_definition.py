"""master data template definition

Revision ID: f7a2c9d4e6b1
Revises: f6c2a8d9e4b1
Create Date: 2026-05-22 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f7a2c9d4e6b1"
down_revision: str | None = "f6c2a8d9e4b1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "master_data_templates",
        sa.Column("definition_json", sa.Text(), nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    op.drop_column("master_data_templates", "definition_json")
