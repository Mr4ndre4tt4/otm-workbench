"""add module ui metadata

Revision ID: f8c4b2a9d6e1
Revises: f7a2c9d4e6b1
Create Date: 2026-05-22 14:02:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f8c4b2a9d6e1"
down_revision: str | None = "f7a2c9d4e6b1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("modules", sa.Column("label_key", sa.String(), nullable=False, server_default=""))
    op.add_column("modules", sa.Column("description", sa.Text(), nullable=False, server_default=""))
    op.add_column("modules", sa.Column("icon_key", sa.String(), nullable=False, server_default="module"))
    op.add_column("modules", sa.Column("icon_family", sa.String(), nullable=False, server_default="iconly"))
    op.add_column("modules", sa.Column("icon_variant", sa.String(), nullable=False, server_default="regular"))
    op.add_column("modules", sa.Column("icon_style", sa.String(), nullable=False, server_default="broken"))
    op.add_column("modules", sa.Column("icon_name", sa.String(), nullable=False, server_default="Folder"))
    op.add_column("modules", sa.Column("icon_light_ref_json", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("modules", sa.Column("icon_dark_ref_json", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("modules", sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("modules", "sort_order")
    op.drop_column("modules", "icon_dark_ref_json")
    op.drop_column("modules", "icon_light_ref_json")
    op.drop_column("modules", "icon_name")
    op.drop_column("modules", "icon_style")
    op.drop_column("modules", "icon_variant")
    op.drop_column("modules", "icon_family")
    op.drop_column("modules", "icon_key")
    op.drop_column("modules", "description")
    op.drop_column("modules", "label_key")
