"""asset links

Revision ID: b7c4e1a9d8f2
Revises: a5d8e2f4c6b9
Create Date: 2026-05-20 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "b7c4e1a9d8f2"
down_revision: str | None = "a5d8e2f4c6b9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "asset_links",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("asset_id", sa.String(), nullable=False),
        sa.Column("link_type", sa.String(), nullable=False),
        sa.Column("target_id", sa.String(), nullable=False),
        sa.Column("target_label", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("asset_id", "created_by", "link_type", "target_id"):
        op.create_index(f"ix_asset_links_{column}", "asset_links", [column])


def downgrade() -> None:
    for column in ("target_id", "link_type", "created_by", "asset_id"):
        op.drop_index(f"ix_asset_links_{column}", table_name="asset_links")
    op.drop_table("asset_links")
