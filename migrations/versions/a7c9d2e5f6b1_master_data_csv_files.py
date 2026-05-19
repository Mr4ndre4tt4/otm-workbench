"""master data csv files

Revision ID: a7c9d2e5f6b1
Revises: f4a8b6c1d2e3
Create Date: 2026-05-19 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "a7c9d2e5f6b1"
down_revision: str | None = "f4a8b6c1d2e3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "master_data_csv_files",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("batch_id", sa.String(), nullable=False),
        sa.Column("template_code", sa.String(), nullable=False),
        sa.Column("table_name", sa.String(), nullable=False),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["master_data_batches.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_master_data_csv_files_batch_id", "master_data_csv_files", ["batch_id"])
    op.create_index("ix_master_data_csv_files_template_code", "master_data_csv_files", ["template_code"])
    op.create_index("ix_master_data_csv_files_table_name", "master_data_csv_files", ["table_name"])


def downgrade() -> None:
    op.drop_index("ix_master_data_csv_files_table_name", table_name="master_data_csv_files")
    op.drop_index("ix_master_data_csv_files_template_code", table_name="master_data_csv_files")
    op.drop_index("ix_master_data_csv_files_batch_id", table_name="master_data_csv_files")
    op.drop_table("master_data_csv_files")
