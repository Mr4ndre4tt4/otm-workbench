"""asset classifications

Revision ID: e8c2b4a9d1f3
Revises: d6b2a9c4e1f8
Create Date: 2026-05-20 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "e8c2b4a9d1f3"
down_revision: str | None = "d6b2a9c4e1f8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "asset_classifications",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("classification_type", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("system_protected", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("classification_type", "code", name="uq_asset_classification_type_code"),
    )
    for column in ("classification_type", "code", "is_active", "sort_order"):
        op.create_index(f"ix_asset_classifications_{column}", "asset_classifications", [column])


def downgrade() -> None:
    for column in ("sort_order", "is_active", "code", "classification_type"):
        op.drop_index(f"ix_asset_classifications_{column}", table_name="asset_classifications")
    op.drop_table("asset_classifications")
