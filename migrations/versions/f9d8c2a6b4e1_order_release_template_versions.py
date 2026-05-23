"""order release template versions

Revision ID: f9d8c2a6b4e1
Revises: f8c4b2a9d6e1
Create Date: 2026-05-23 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f9d8c2a6b4e1"
down_revision: str | None = "f8c4b2a9d6e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table(
        "order_release_templates",
        recreate="always",
        table_args=(sa.UniqueConstraint("code", "version", name="uq_order_release_templates_code_version"),),
    ):
        pass


def downgrade() -> None:
    with op.batch_alter_table(
        "order_release_templates",
        recreate="always",
        table_args=(sa.UniqueConstraint("code", name="uq_order_release_templates_code"),),
    ):
        pass
