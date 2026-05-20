"""module navigation metadata

Revision ID: f6b2d4a8c1e9
Revises: f5e1b6d9a2c8
Create Date: 2026-05-20 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "f6b2d4a8c1e9"
down_revision: str | None = "f5e1b6d9a2c8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


MODULE_METADATA = {
    "home": {
        "group_key": "cockpit",
        "group_label": "Cockpit",
        "icon_key": "layout-dashboard",
        "sort_order": 100,
        "surface_type": "workspace",
        "description": "Project cockpit and operational overview.",
        "is_primary": True,
    },
    "evidence": {
        "group_key": "cockpit",
        "group_label": "Cockpit",
        "icon_key": "archive",
        "sort_order": 120,
        "surface_type": "workspace",
        "description": "Browse client-safe evidence, manifests and linked artifacts.",
        "is_primary": True,
    },
    "master_data": {
        "group_key": "build",
        "group_label": "Build",
        "icon_key": "database",
        "sort_order": 210,
        "surface_type": "module",
        "description": "Create and validate reusable OTM master data load templates.",
        "is_primary": True,
    },
    "rates": {
        "group_key": "build",
        "group_label": "Build",
        "icon_key": "badge-dollar-sign",
        "sort_order": 220,
        "surface_type": "module",
        "description": "Prepare, validate, approve and export OTM rates packages.",
        "is_primary": True,
    },
    "order_release_generator": {
        "group_key": "build",
        "group_label": "Build",
        "icon_key": "file-plus-2",
        "sort_order": 240,
        "surface_type": "module",
        "description": "Generate synthetic Order Release XML payloads for OTM tests.",
        "is_primary": True,
    },
    "integration_mapping": {
        "group_key": "build",
        "group_label": "Build",
        "icon_key": "git-branch",
        "sort_order": 250,
        "surface_type": "module",
        "description": "Model source-to-target payload mappings and generate integration specs.",
        "is_primary": True,
    },
    "catalog": {
        "group_key": "govern",
        "group_label": "Govern",
        "icon_key": "book-open",
        "sort_order": 310,
        "surface_type": "reference",
        "description": "Explore OTM Data Dictionary objects, columns and load plans.",
        "is_primary": True,
    },
    "load_plan": {
        "group_key": "govern",
        "group_label": "Govern",
        "icon_key": "list-checks",
        "sort_order": 320,
        "surface_type": "module",
        "description": "Create load packages, cutover readiness and CSVUTIL handoff assets.",
        "is_primary": True,
    },
    "assets": {
        "group_key": "govern",
        "group_label": "Govern",
        "icon_key": "folder-open",
        "sort_order": 330,
        "surface_type": "library",
        "description": "Manage reusable files, templates and module-linked assets.",
        "is_primary": True,
    },
    "admin": {
        "group_key": "admin",
        "group_label": "Admin",
        "icon_key": "settings",
        "sort_order": 410,
        "surface_type": "admin",
        "description": "Manage project, profile, environment and administrative settings.",
        "is_primary": True,
    },
    "dev_tools": {
        "group_key": "admin",
        "group_label": "Admin",
        "icon_key": "terminal",
        "sort_order": 490,
        "surface_type": "developer",
        "description": "Developer-only diagnostics and internal tools.",
        "is_primary": False,
    },
}


def upgrade() -> None:
    op.add_column("modules", sa.Column("group_key", sa.String(), nullable=False, server_default="build"))
    op.add_column("modules", sa.Column("group_label", sa.String(), nullable=False, server_default="Build"))
    op.add_column("modules", sa.Column("icon_key", sa.String(), nullable=False, server_default="box"))
    op.add_column("modules", sa.Column("sort_order", sa.Integer(), nullable=False, server_default="500"))
    op.add_column("modules", sa.Column("surface_type", sa.String(), nullable=False, server_default="module"))
    op.add_column("modules", sa.Column("description", sa.Text(), nullable=False, server_default=""))
    op.add_column("modules", sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.true()))

    modules = sa.table(
        "modules",
        sa.column("id", sa.String()),
        sa.column("group_key", sa.String()),
        sa.column("group_label", sa.String()),
        sa.column("icon_key", sa.String()),
        sa.column("sort_order", sa.Integer()),
        sa.column("surface_type", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("is_primary", sa.Boolean()),
    )
    for module_id, metadata in MODULE_METADATA.items():
        op.execute(
            modules.update()
            .where(modules.c.id == module_id)
            .values(**metadata)
        )


def downgrade() -> None:
    if "modules" not in inspect(op.get_bind()).get_table_names():
        return
    op.drop_column("modules", "is_primary")
    op.drop_column("modules", "description")
    op.drop_column("modules", "surface_type")
    op.drop_column("modules", "sort_order")
    op.drop_column("modules", "icon_key")
    op.drop_column("modules", "group_label")
    op.drop_column("modules", "group_key")
