"""load plan package intake

Revision ID: d2f7b9c4a8e3
Revises: c9f2a8d4e6b1
Create Date: 2026-05-18 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d2f7b9c4a8e3"
down_revision: Union[str, None] = "c9f2a8d4e6b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "load_plan_packages",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("environment_id", sa.String(), nullable=True),
        sa.Column("profile_id", sa.String(), nullable=True),
        sa.Column("source_module", sa.String(), nullable=False),
        sa.Column("source_entity_type", sa.String(), nullable=False),
        sa.Column("source_entity_id", sa.String(), nullable=False),
        sa.Column("package_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("artifact_id", sa.String(), nullable=True),
        sa.Column("manifest_id", sa.String(), nullable=True),
        sa.Column("evidence_id", sa.String(), nullable=True),
        sa.Column("approval_evidence_id", sa.String(), nullable=True),
        sa.Column("load_sequence_json", sa.Text(), nullable=False),
        sa.Column("summary_json", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("registered_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_load_plan_packages_project_id"), "load_plan_packages", ["project_id"])
    op.create_index(op.f("ix_load_plan_packages_environment_id"), "load_plan_packages", ["environment_id"])
    op.create_index(op.f("ix_load_plan_packages_profile_id"), "load_plan_packages", ["profile_id"])
    op.create_index(op.f("ix_load_plan_packages_source_module"), "load_plan_packages", ["source_module"])
    op.create_index(op.f("ix_load_plan_packages_source_entity_type"), "load_plan_packages", ["source_entity_type"])
    op.create_index(op.f("ix_load_plan_packages_source_entity_id"), "load_plan_packages", ["source_entity_id"])
    op.create_index(op.f("ix_load_plan_packages_package_type"), "load_plan_packages", ["package_type"])
    op.create_index(op.f("ix_load_plan_packages_status"), "load_plan_packages", ["status"])
    op.create_index(op.f("ix_load_plan_packages_artifact_id"), "load_plan_packages", ["artifact_id"])
    op.create_index(op.f("ix_load_plan_packages_manifest_id"), "load_plan_packages", ["manifest_id"])
    op.create_index(op.f("ix_load_plan_packages_evidence_id"), "load_plan_packages", ["evidence_id"])
    op.create_index(
        op.f("ix_load_plan_packages_approval_evidence_id"),
        "load_plan_packages",
        ["approval_evidence_id"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_load_plan_packages_approval_evidence_id"), table_name="load_plan_packages")
    op.drop_index(op.f("ix_load_plan_packages_evidence_id"), table_name="load_plan_packages")
    op.drop_index(op.f("ix_load_plan_packages_manifest_id"), table_name="load_plan_packages")
    op.drop_index(op.f("ix_load_plan_packages_artifact_id"), table_name="load_plan_packages")
    op.drop_index(op.f("ix_load_plan_packages_status"), table_name="load_plan_packages")
    op.drop_index(op.f("ix_load_plan_packages_package_type"), table_name="load_plan_packages")
    op.drop_index(op.f("ix_load_plan_packages_source_entity_id"), table_name="load_plan_packages")
    op.drop_index(op.f("ix_load_plan_packages_source_entity_type"), table_name="load_plan_packages")
    op.drop_index(op.f("ix_load_plan_packages_source_module"), table_name="load_plan_packages")
    op.drop_index(op.f("ix_load_plan_packages_profile_id"), table_name="load_plan_packages")
    op.drop_index(op.f("ix_load_plan_packages_environment_id"), table_name="load_plan_packages")
    op.drop_index(op.f("ix_load_plan_packages_project_id"), table_name="load_plan_packages")
    op.drop_table("load_plan_packages")
