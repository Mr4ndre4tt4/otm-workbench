"""load plan sequence snapshots

Revision ID: f2a6c8d1e9b4
Revises: c7d2f4a9e1b5
Create Date: 2026-05-18 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f2a6c8d1e9b4"
down_revision: str | None = "c7d2f4a9e1b5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "load_plan_sequence_snapshots",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("environment_id", sa.String(), nullable=True),
        sa.Column("profile_id", sa.String(), nullable=True),
        sa.Column("package_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("sequence_json", sa.Text(), nullable=False),
        sa.Column("blockers_json", sa.Text(), nullable=False),
        sa.Column("summary_json", sa.Text(), nullable=False),
        sa.Column("evidence_id", sa.String(), nullable=True),
        sa.Column("generated_by", sa.String(), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
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
        "evidence_id",
        "generated_by",
        "generated_at",
    ]:
        op.create_index(
            f"ix_load_plan_sequence_snapshots_{column}",
            "load_plan_sequence_snapshots",
            [column],
        )


def downgrade() -> None:
    for column in [
        "generated_at",
        "generated_by",
        "evidence_id",
        "status",
        "package_id",
        "profile_id",
        "environment_id",
        "project_id",
    ]:
        op.drop_index(f"ix_load_plan_sequence_snapshots_{column}", table_name="load_plan_sequence_snapshots")
    op.drop_table("load_plan_sequence_snapshots")
