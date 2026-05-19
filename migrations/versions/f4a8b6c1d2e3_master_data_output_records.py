"""master data output records

Revision ID: f4a8b6c1d2e3
Revises: e2b7c4d5a9f0
Create Date: 2026-05-19 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f4a8b6c1d2e3"
down_revision: str | None = "e2b7c4d5a9f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "master_data_output_records",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("batch_id", sa.String(), nullable=False),
        sa.Column("template_code", sa.String(), nullable=False),
        sa.Column("target_table", sa.String(), nullable=False),
        sa.Column("record_index", sa.Integer(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["master_data_batches.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_master_data_output_records_batch_id", "master_data_output_records", ["batch_id"])
    op.create_index(
        "ix_master_data_output_records_template_code",
        "master_data_output_records",
        ["template_code"],
    )
    op.create_index(
        "ix_master_data_output_records_target_table",
        "master_data_output_records",
        ["target_table"],
    )


def downgrade() -> None:
    op.drop_index("ix_master_data_output_records_target_table", table_name="master_data_output_records")
    op.drop_index("ix_master_data_output_records_template_code", table_name="master_data_output_records")
    op.drop_index("ix_master_data_output_records_batch_id", table_name="master_data_output_records")
    op.drop_table("master_data_output_records")
