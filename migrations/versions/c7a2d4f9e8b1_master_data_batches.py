"""master data batches

Revision ID: c7a2d4f9e8b1
Revises: b8e4f2a9c1d6
Create Date: 2026-05-19 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c7a2d4f9e8b1"
down_revision: str | None = "b8e4f2a9c1d6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "master_data_batches",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("template_id", sa.String(), nullable=False),
        sa.Column("template_code", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("sheet_summaries_json", sa.Text(), nullable=False),
        sa.Column("parsed_rows_json", sa.Text(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("issue_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["template_id"], ["master_data_templates.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_master_data_batches_template_code", "master_data_batches", ["template_code"])
    op.create_index("ix_master_data_batches_template_id", "master_data_batches", ["template_id"])


def downgrade() -> None:
    op.drop_index("ix_master_data_batches_template_id", table_name="master_data_batches")
    op.drop_index("ix_master_data_batches_template_code", table_name="master_data_batches")
    op.drop_table("master_data_batches")
