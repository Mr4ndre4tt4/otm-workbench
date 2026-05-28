"""assets target otm version

Revision ID: c1f4a8e7d9b2
Revises: feb6c9d1a2e4
Create Date: 2026-05-28 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c1f4a8e7d9b2"
down_revision: str | None = "feb6c9d1a2e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("assets", sa.Column("target_otm_version", sa.String(), nullable=True))
    op.create_index("ix_assets_target_otm_version", "assets", ["target_otm_version"])


def downgrade() -> None:
    op.drop_index("ix_assets_target_otm_version", table_name="assets")
    op.drop_column("assets", "target_otm_version")
