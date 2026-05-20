"""assets

Revision ID: f9a7d3c5b2e1
Revises: e8c2b4a9d1f3
Create Date: 2026-05-20 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f9a7d3c5b2e1"
down_revision: str | None = "e8c2b4a9d1f3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "assets",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("profile_id", sa.String(), nullable=True),
        sa.Column("environment_id", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("asset_type", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("visibility", sa.String(), nullable=False),
        sa.Column("scope_type", sa.String(), nullable=False),
        sa.Column("sensitivity", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("module_id", sa.String(), nullable=True),
        sa.Column("macro_object_code", sa.String(), nullable=True),
        sa.Column("otm_table_name", sa.String(), nullable=True),
        sa.Column("tags_json", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "asset_type",
        "category",
        "created_by",
        "environment_id",
        "macro_object_code",
        "module_id",
        "otm_table_name",
        "profile_id",
        "project_id",
        "scope_type",
        "sensitivity",
        "status",
        "visibility",
    ):
        op.create_index(f"ix_assets_{column}", "assets", [column])


def downgrade() -> None:
    for column in (
        "visibility",
        "status",
        "sensitivity",
        "scope_type",
        "project_id",
        "profile_id",
        "otm_table_name",
        "module_id",
        "macro_object_code",
        "environment_id",
        "created_by",
        "category",
        "asset_type",
    ):
        op.drop_index(f"ix_assets_{column}", table_name="assets")
    op.drop_table("assets")
