"""rates batch contract

Revision ID: c9f2a8d4e6b1
Revises: b7d4a6f1c2a9
Create Date: 2026-05-18 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c9f2a8d4e6b1"
down_revision: Union[str, None] = "b7d4a6f1c2a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rate_batches",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("environment_id", sa.String(), nullable=True),
        sa.Column("profile_id", sa.String(), nullable=True),
        sa.Column("scenario_code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("domain_name", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("validated_at", sa.DateTime(), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("exported_at", sa.DateTime(), nullable=True),
        sa.Column("summary_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rate_batches_project_id"), "rate_batches", ["project_id"])
    op.create_index(op.f("ix_rate_batches_environment_id"), "rate_batches", ["environment_id"])
    op.create_index(op.f("ix_rate_batches_profile_id"), "rate_batches", ["profile_id"])
    op.create_index(op.f("ix_rate_batches_scenario_code"), "rate_batches", ["scenario_code"])
    op.create_index(op.f("ix_rate_batches_status"), "rate_batches", ["status"])
    op.create_index(op.f("ix_rate_batches_domain_name"), "rate_batches", ["domain_name"])

    op.create_table(
        "rate_batch_tables",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("batch_id", sa.String(), nullable=False),
        sa.Column("table_name", sa.String(), nullable=False),
        sa.Column("sequence_index", sa.Integer(), nullable=False),
        sa.Column("requirement_level", sa.String(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["rate_batches.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rate_batch_tables_batch_id"), "rate_batch_tables", ["batch_id"])
    op.create_index(op.f("ix_rate_batch_tables_table_name"), "rate_batch_tables", ["table_name"])
    op.create_index(op.f("ix_rate_batch_tables_status"), "rate_batch_tables", ["status"])

    op.create_table(
        "rate_batch_rows",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("batch_id", sa.String(), nullable=False),
        sa.Column("batch_table_id", sa.String(), nullable=False),
        sa.Column("table_name", sa.String(), nullable=False),
        sa.Column("row_index", sa.Integer(), nullable=False),
        sa.Column("row_payload_json", sa.Text(), nullable=False),
        sa.Column("normalized_payload_json", sa.Text(), nullable=False),
        sa.Column("row_hash", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["rate_batches.id"]),
        sa.ForeignKeyConstraint(["batch_table_id"], ["rate_batch_tables.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rate_batch_rows_batch_id"), "rate_batch_rows", ["batch_id"])
    op.create_index(op.f("ix_rate_batch_rows_batch_table_id"), "rate_batch_rows", ["batch_table_id"])
    op.create_index(op.f("ix_rate_batch_rows_table_name"), "rate_batch_rows", ["table_name"])
    op.create_index(op.f("ix_rate_batch_rows_row_hash"), "rate_batch_rows", ["row_hash"])
    op.create_index(op.f("ix_rate_batch_rows_status"), "rate_batch_rows", ["status"])

    op.create_table(
        "rate_batch_issues",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("batch_id", sa.String(), nullable=False),
        sa.Column("batch_table_id", sa.String(), nullable=True),
        sa.Column("batch_row_id", sa.String(), nullable=True),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("issue_code", sa.String(), nullable=False),
        sa.Column("table_name", sa.String(), nullable=True),
        sa.Column("column_name", sa.String(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["rate_batches.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rate_batch_issues_batch_id"), "rate_batch_issues", ["batch_id"])
    op.create_index(op.f("ix_rate_batch_issues_batch_table_id"), "rate_batch_issues", ["batch_table_id"])
    op.create_index(op.f("ix_rate_batch_issues_batch_row_id"), "rate_batch_issues", ["batch_row_id"])
    op.create_index(op.f("ix_rate_batch_issues_severity"), "rate_batch_issues", ["severity"])
    op.create_index(op.f("ix_rate_batch_issues_issue_code"), "rate_batch_issues", ["issue_code"])
    op.create_index(op.f("ix_rate_batch_issues_table_name"), "rate_batch_issues", ["table_name"])


def downgrade() -> None:
    op.drop_index(op.f("ix_rate_batch_issues_table_name"), table_name="rate_batch_issues")
    op.drop_index(op.f("ix_rate_batch_issues_issue_code"), table_name="rate_batch_issues")
    op.drop_index(op.f("ix_rate_batch_issues_severity"), table_name="rate_batch_issues")
    op.drop_index(op.f("ix_rate_batch_issues_batch_row_id"), table_name="rate_batch_issues")
    op.drop_index(op.f("ix_rate_batch_issues_batch_table_id"), table_name="rate_batch_issues")
    op.drop_index(op.f("ix_rate_batch_issues_batch_id"), table_name="rate_batch_issues")
    op.drop_table("rate_batch_issues")

    op.drop_index(op.f("ix_rate_batch_rows_status"), table_name="rate_batch_rows")
    op.drop_index(op.f("ix_rate_batch_rows_row_hash"), table_name="rate_batch_rows")
    op.drop_index(op.f("ix_rate_batch_rows_table_name"), table_name="rate_batch_rows")
    op.drop_index(op.f("ix_rate_batch_rows_batch_table_id"), table_name="rate_batch_rows")
    op.drop_index(op.f("ix_rate_batch_rows_batch_id"), table_name="rate_batch_rows")
    op.drop_table("rate_batch_rows")

    op.drop_index(op.f("ix_rate_batch_tables_status"), table_name="rate_batch_tables")
    op.drop_index(op.f("ix_rate_batch_tables_table_name"), table_name="rate_batch_tables")
    op.drop_index(op.f("ix_rate_batch_tables_batch_id"), table_name="rate_batch_tables")
    op.drop_table("rate_batch_tables")

    op.drop_index(op.f("ix_rate_batches_domain_name"), table_name="rate_batches")
    op.drop_index(op.f("ix_rate_batches_status"), table_name="rate_batches")
    op.drop_index(op.f("ix_rate_batches_scenario_code"), table_name="rate_batches")
    op.drop_index(op.f("ix_rate_batches_profile_id"), table_name="rate_batches")
    op.drop_index(op.f("ix_rate_batches_environment_id"), table_name="rate_batches")
    op.drop_index(op.f("ix_rate_batches_project_id"), table_name="rate_batches")
    op.drop_table("rate_batches")
