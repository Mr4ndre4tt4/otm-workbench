"""load plan readiness exports

Revision ID: d4e9b2c7a6f1
Revises: a8d3e5f7b2c1
Create Date: 2026-05-18 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "d4e9b2c7a6f1"
down_revision: str | None = "a8d3e5f7b2c1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "load_plan_readiness_exports",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("environment_id", sa.String(), nullable=True),
        sa.Column("profile_id", sa.String(), nullable=True),
        sa.Column("package_id", sa.String(), nullable=False),
        sa.Column("readiness_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("artifact_id", sa.String(), nullable=True),
        sa.Column("manifest_id", sa.String(), nullable=True),
        sa.Column("evidence_id", sa.String(), nullable=True),
        sa.Column("summary_json", sa.Text(), nullable=False),
        sa.Column("exported_by", sa.String(), nullable=True),
        sa.Column("exported_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["package_id"], ["load_plan_packages.id"]),
        sa.ForeignKeyConstraint(["readiness_id"], ["load_plan_cutover_readiness.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in [
        "project_id",
        "environment_id",
        "profile_id",
        "package_id",
        "readiness_id",
        "status",
        "artifact_id",
        "manifest_id",
        "evidence_id",
        "exported_by",
        "exported_at",
    ]:
        op.create_index(
            f"ix_load_plan_readiness_exports_{column}",
            "load_plan_readiness_exports",
            [column],
        )


def downgrade() -> None:
    for column in [
        "exported_at",
        "exported_by",
        "evidence_id",
        "manifest_id",
        "artifact_id",
        "status",
        "readiness_id",
        "package_id",
        "profile_id",
        "environment_id",
        "project_id",
    ]:
        op.drop_index(
            f"ix_load_plan_readiness_exports_{column}",
            table_name="load_plan_readiness_exports",
        )
    op.drop_table("load_plan_readiness_exports")
