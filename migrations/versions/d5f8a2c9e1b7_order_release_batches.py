"""order release batches

Revision ID: d5f8a2c9e1b7
Revises: c2e9f4a7b6d1
Create Date: 2026-05-20 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "d5f8a2c9e1b7"
down_revision: str | None = "c2e9f4a7b6d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "order_release_batches",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("template_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("release_count", sa.Integer(), nullable=False),
        sa.Column("issue_count", sa.Integer(), nullable=False),
        sa.Column("summary_json", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["template_id"], ["order_release_templates.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("created_by", "status", "template_id"):
        op.create_index(f"ix_order_release_batches_{column}", "order_release_batches", [column])

    op.create_table(
        "order_release_batch_rows",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("batch_id", sa.String(), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("release_gid", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("normalized_json", sa.Text(), nullable=False),
        sa.Column("issues_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["order_release_batches.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("batch_id", "release_gid", "row_number", "status"):
        op.create_index(f"ix_order_release_batch_rows_{column}", "order_release_batch_rows", [column])


def downgrade() -> None:
    for column in ("status", "row_number", "release_gid", "batch_id"):
        op.drop_index(f"ix_order_release_batch_rows_{column}", table_name="order_release_batch_rows")
    op.drop_table("order_release_batch_rows")
    for column in ("template_id", "status", "created_by"):
        op.drop_index(f"ix_order_release_batches_{column}", table_name="order_release_batches")
    op.drop_table("order_release_batches")
