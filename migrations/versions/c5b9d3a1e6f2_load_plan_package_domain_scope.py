"""load plan package domain scope

Revision ID: c5b9d3a1e6f2
Revises: c4a8e2f7b9d1
Create Date: 2026-05-28 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c5b9d3a1e6f2"
down_revision: str | None = "c4a8e2f7b9d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def table_columns(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def index_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    if "domain_name" not in table_columns("load_plan_packages"):
        op.add_column("load_plan_packages", sa.Column("domain_name", sa.String(), nullable=True))

    index_name = "ix_load_plan_packages_domain_name"
    if index_name not in index_names("load_plan_packages"):
        op.create_index(index_name, "load_plan_packages", ["domain_name"])


def downgrade() -> None:
    index_name = "ix_load_plan_packages_domain_name"
    if index_name in index_names("load_plan_packages"):
        op.drop_index(index_name, table_name="load_plan_packages")

    if "domain_name" in table_columns("load_plan_packages"):
        op.drop_column("load_plan_packages", "domain_name")
