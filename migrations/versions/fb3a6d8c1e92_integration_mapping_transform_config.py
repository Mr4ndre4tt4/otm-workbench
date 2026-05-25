"""integration mapping transform config

Revision ID: fb3a6d8c1e92
Revises: fa2b7c9d4e6f
Create Date: 2026-05-25 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "fb3a6d8c1e92"
down_revision: str | None = "fa2b7c9d4e6f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "integration_mappings",
        sa.Column("transform_config_json", sa.Text(), nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    op.drop_column("integration_mappings", "transform_config_json")
