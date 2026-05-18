"""load plan zip analysis

Revision ID: a4c8e2f9b6d3
Revises: e8a1c5d9f0b2
Create Date: 2026-05-18 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "a4c8e2f9b6d3"
down_revision: str | None = "e8a1c5d9f0b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "load_plan_zip_analyses",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("environment_id", sa.String(), nullable=True),
        sa.Column("profile_id", sa.String(), nullable=True),
        sa.Column("package_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("source_artifact_id", sa.String(), nullable=True),
        sa.Column("source_manifest_id", sa.String(), nullable=True),
        sa.Column("manifest_id", sa.String(), nullable=True),
        sa.Column("evidence_id", sa.String(), nullable=True),
        sa.Column("summary_json", sa.Text(), nullable=False),
        sa.Column("findings_json", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["package_id"], ["load_plan_packages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in [
        "project_id",
        "environment_id",
        "profile_id",
        "package_id",
        "status",
        "source_artifact_id",
        "source_manifest_id",
        "manifest_id",
        "evidence_id",
    ]:
        op.create_index(
            f"ix_load_plan_zip_analyses_{column}",
            "load_plan_zip_analyses",
            [column],
        )


def downgrade() -> None:
    for column in [
        "evidence_id",
        "manifest_id",
        "source_manifest_id",
        "source_artifact_id",
        "status",
        "package_id",
        "profile_id",
        "environment_id",
        "project_id",
    ]:
        op.drop_index(f"ix_load_plan_zip_analyses_{column}", table_name="load_plan_zip_analyses")
    op.drop_table("load_plan_zip_analyses")
