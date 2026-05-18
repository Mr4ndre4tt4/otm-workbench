"""load plan cutover handoffs

Revision ID: e6b1c9d4a7f2
Revises: d4e9b2c7a6f1
Create Date: 2026-05-18 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "e6b1c9d4a7f2"
down_revision: str | None = "d4e9b2c7a6f1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "load_plan_cutover_handoffs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("environment_id", sa.String(), nullable=True),
        sa.Column("profile_id", sa.String(), nullable=True),
        sa.Column("package_id", sa.String(), nullable=False),
        sa.Column("readiness_id", sa.String(), nullable=False),
        sa.Column("readiness_export_id", sa.String(), nullable=False),
        sa.Column("archive_evidence_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("evidence_id", sa.String(), nullable=True),
        sa.Column("summary_json", sa.Text(), nullable=False),
        sa.Column("committed_by", sa.String(), nullable=True),
        sa.Column("committed_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["package_id"], ["load_plan_packages.id"]),
        sa.ForeignKeyConstraint(["readiness_id"], ["load_plan_cutover_readiness.id"]),
        sa.ForeignKeyConstraint(["readiness_export_id"], ["load_plan_readiness_exports.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in [
        "project_id",
        "environment_id",
        "profile_id",
        "package_id",
        "readiness_id",
        "readiness_export_id",
        "archive_evidence_id",
        "status",
        "evidence_id",
        "committed_by",
        "committed_at",
    ]:
        op.create_index(
            f"ix_load_plan_cutover_handoffs_{column}",
            "load_plan_cutover_handoffs",
            [column],
        )


def downgrade() -> None:
    for column in [
        "committed_at",
        "committed_by",
        "evidence_id",
        "status",
        "archive_evidence_id",
        "readiness_export_id",
        "readiness_id",
        "package_id",
        "profile_id",
        "environment_id",
        "project_id",
    ]:
        op.drop_index(f"ix_load_plan_cutover_handoffs_{column}", table_name="load_plan_cutover_handoffs")
    op.drop_table("load_plan_cutover_handoffs")
