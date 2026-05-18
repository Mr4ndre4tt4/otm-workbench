"""load plan csvutil builder

Revision ID: e8a1c5d9f0b2
Revises: d2f7b9c4a8e3
Create Date: 2026-05-18 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e8a1c5d9f0b2"
down_revision: Union[str, None] = "d2f7b9c4a8e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "csvutil_builds",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("environment_id", sa.String(), nullable=True),
        sa.Column("profile_id", sa.String(), nullable=True),
        sa.Column("package_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("ctl_artifact_id", sa.String(), nullable=True),
        sa.Column("cl_artifact_id", sa.String(), nullable=True),
        sa.Column("manifest_id", sa.String(), nullable=True),
        sa.Column("evidence_id", sa.String(), nullable=True),
        sa.Column("summary_json", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("built_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["package_id"], ["load_plan_packages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_csvutil_builds_project_id"), "csvutil_builds", ["project_id"])
    op.create_index(op.f("ix_csvutil_builds_environment_id"), "csvutil_builds", ["environment_id"])
    op.create_index(op.f("ix_csvutil_builds_profile_id"), "csvutil_builds", ["profile_id"])
    op.create_index(op.f("ix_csvutil_builds_package_id"), "csvutil_builds", ["package_id"])
    op.create_index(op.f("ix_csvutil_builds_status"), "csvutil_builds", ["status"])
    op.create_index(op.f("ix_csvutil_builds_ctl_artifact_id"), "csvutil_builds", ["ctl_artifact_id"])
    op.create_index(op.f("ix_csvutil_builds_cl_artifact_id"), "csvutil_builds", ["cl_artifact_id"])
    op.create_index(op.f("ix_csvutil_builds_manifest_id"), "csvutil_builds", ["manifest_id"])
    op.create_index(op.f("ix_csvutil_builds_evidence_id"), "csvutil_builds", ["evidence_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_csvutil_builds_evidence_id"), table_name="csvutil_builds")
    op.drop_index(op.f("ix_csvutil_builds_manifest_id"), table_name="csvutil_builds")
    op.drop_index(op.f("ix_csvutil_builds_cl_artifact_id"), table_name="csvutil_builds")
    op.drop_index(op.f("ix_csvutil_builds_ctl_artifact_id"), table_name="csvutil_builds")
    op.drop_index(op.f("ix_csvutil_builds_status"), table_name="csvutil_builds")
    op.drop_index(op.f("ix_csvutil_builds_package_id"), table_name="csvutil_builds")
    op.drop_index(op.f("ix_csvutil_builds_profile_id"), table_name="csvutil_builds")
    op.drop_index(op.f("ix_csvutil_builds_environment_id"), table_name="csvutil_builds")
    op.drop_index(op.f("ix_csvutil_builds_project_id"), table_name="csvutil_builds")
    op.drop_table("csvutil_builds")
