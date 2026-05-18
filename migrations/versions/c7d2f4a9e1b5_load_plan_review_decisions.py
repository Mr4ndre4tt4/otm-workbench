"""load plan review decisions

Revision ID: c7d2f4a9e1b5
Revises: b9e6d1c4f8a2
Create Date: 2026-05-18 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c7d2f4a9e1b5"
down_revision: str | None = "b9e6d1c4f8a2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "load_plan_review_decisions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("environment_id", sa.String(), nullable=True),
        sa.Column("profile_id", sa.String(), nullable=True),
        sa.Column("package_id", sa.String(), nullable=False),
        sa.Column("review_item_id", sa.String(), nullable=False),
        sa.Column("decision_status", sa.String(), nullable=False),
        sa.Column("decision_note", sa.Text(), nullable=False),
        sa.Column("evidence_id", sa.String(), nullable=True),
        sa.Column("decided_by", sa.String(), nullable=True),
        sa.Column("decided_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["package_id"], ["load_plan_packages.id"]),
        sa.ForeignKeyConstraint(["review_item_id"], ["load_plan_review_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in [
        "project_id",
        "environment_id",
        "profile_id",
        "package_id",
        "review_item_id",
        "decision_status",
        "evidence_id",
        "decided_by",
    ]:
        op.create_index(
            f"ix_load_plan_review_decisions_{column}",
            "load_plan_review_decisions",
            [column],
        )


def downgrade() -> None:
    for column in [
        "decided_by",
        "evidence_id",
        "decision_status",
        "review_item_id",
        "package_id",
        "profile_id",
        "environment_id",
        "project_id",
    ]:
        op.drop_index(f"ix_load_plan_review_decisions_{column}", table_name="load_plan_review_decisions")
    op.drop_table("load_plan_review_decisions")
