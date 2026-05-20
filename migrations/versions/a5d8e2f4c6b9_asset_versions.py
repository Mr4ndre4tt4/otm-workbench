"""asset versions

Revision ID: a5d8e2f4c6b9
Revises: f9a7d3c5b2e1
Create Date: 2026-05-20 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "a5d8e2f4c6b9"
down_revision: str | None = "f9a7d3c5b2e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("assets", sa.Column("current_version_id", sa.String(), nullable=True))
    op.create_index("ix_assets_current_version_id", "assets", ["current_version_id"])
    op.create_table(
        "asset_versions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("asset_id", sa.String(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("storage_path", sa.String(), nullable=False),
        sa.Column("sha256", sa.String(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("uploaded_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("asset_id", "sha256", "status", "uploaded_by", "version_number"):
        op.create_index(f"ix_asset_versions_{column}", "asset_versions", [column])


def downgrade() -> None:
    for column in ("version_number", "uploaded_by", "status", "sha256", "asset_id"):
        op.drop_index(f"ix_asset_versions_{column}", table_name="asset_versions")
    op.drop_table("asset_versions")
    op.drop_index("ix_assets_current_version_id", table_name="assets")
    op.drop_column("assets", "current_version_id")
