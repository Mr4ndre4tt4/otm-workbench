"""order release templates

Revision ID: c2e9f4a7b6d1
Revises: b7c4e1a9d8f2
Create Date: 2026-05-20 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c2e9f4a7b6d1"
down_revision: str | None = "b7c4e1a9d8f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "order_release_templates",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("macro_object_code", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("required_columns_json", sa.Text(), nullable=False),
        sa.Column("optional_columns_json", sa.Text(), nullable=False),
        sa.Column("defaults_json", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    for column in ("code", "created_by", "macro_object_code", "status", "version"):
        op.create_index(f"ix_order_release_templates_{column}", "order_release_templates", [column])


def downgrade() -> None:
    for column in ("version", "status", "macro_object_code", "created_by", "code"):
        op.drop_index(f"ix_order_release_templates_{column}", table_name="order_release_templates")
    op.drop_table("order_release_templates")
