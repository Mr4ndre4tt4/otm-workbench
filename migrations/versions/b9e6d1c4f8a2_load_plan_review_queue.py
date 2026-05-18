"""load plan review queue

Revision ID: b9e6d1c4f8a2
Revises: a4c8e2f9b6d3
Create Date: 2026-05-18 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "b9e6d1c4f8a2"
down_revision: str | None = "a4c8e2f9b6d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "load_plan_review_items",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("environment_id", sa.String(), nullable=True),
        sa.Column("profile_id", sa.String(), nullable=True),
        sa.Column("package_id", sa.String(), nullable=False),
        sa.Column("zip_analysis_id", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("source_code", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("table_name", sa.String(), nullable=True),
        sa.Column("file_name", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["package_id"], ["load_plan_packages.id"]),
        sa.ForeignKeyConstraint(["zip_analysis_id"], ["load_plan_zip_analyses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in [
        "project_id",
        "environment_id",
        "profile_id",
        "package_id",
        "zip_analysis_id",
        "source_type",
        "source_code",
        "severity",
        "status",
        "category",
        "table_name",
    ]:
        op.create_index(
            f"ix_load_plan_review_items_{column}",
            "load_plan_review_items",
            [column],
        )


def downgrade() -> None:
    for column in [
        "table_name",
        "category",
        "status",
        "severity",
        "source_code",
        "source_type",
        "zip_analysis_id",
        "package_id",
        "profile_id",
        "environment_id",
        "project_id",
    ]:
        op.drop_index(f"ix_load_plan_review_items_{column}", table_name="load_plan_review_items")
    op.drop_table("load_plan_review_items")
