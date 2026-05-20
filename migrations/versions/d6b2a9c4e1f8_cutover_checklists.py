"""cutover checklists

Revision ID: d6b2a9c4e1f8
Revises: c3a8f7b2d9e4
Create Date: 2026-05-20 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "d6b2a9c4e1f8"
down_revision: str | None = "c3a8f7b2d9e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cutover_checklist_templates",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("system_seeded", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_cutover_checklist_templates_code", "cutover_checklist_templates", ["code"])
    op.create_index("ix_cutover_checklist_templates_status", "cutover_checklist_templates", ["status"])
    op.create_table(
        "cutover_checklist_template_items",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("template_id", sa.String(), nullable=False),
        sa.Column("item_code", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("default_method", sa.String(), nullable=False),
        sa.Column("applies_to_package_type", sa.String(), nullable=False),
        sa.Column("required_evidence_type", sa.String(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["template_id"], ["cutover_checklist_templates.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_cutover_checklist_template_items_item_code",
        "cutover_checklist_template_items",
        ["item_code"],
    )
    op.create_index(
        "ix_cutover_checklist_template_items_sort_order",
        "cutover_checklist_template_items",
        ["sort_order"],
    )
    op.create_index(
        "ix_cutover_checklist_template_items_template_id",
        "cutover_checklist_template_items",
        ["template_id"],
    )
    op.create_table(
        "cutover_checklists",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("environment_id", sa.String(), nullable=True),
        sa.Column("profile_id", sa.String(), nullable=True),
        sa.Column("template_id", sa.String(), nullable=False),
        sa.Column("package_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("package_type", sa.String(), nullable=False),
        sa.Column("catalog_macro_object_code", sa.String(), nullable=True),
        sa.Column("summary_json", sa.Text(), nullable=False),
        sa.Column("evidence_id", sa.String(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["package_id"], ["load_plan_packages.id"]),
        sa.ForeignKeyConstraint(["template_id"], ["cutover_checklist_templates.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "catalog_macro_object_code",
        "created_by",
        "environment_id",
        "evidence_id",
        "package_id",
        "package_type",
        "profile_id",
        "project_id",
        "status",
        "template_id",
    ):
        op.create_index(f"ix_cutover_checklists_{column}", "cutover_checklists", [column])
    op.create_table(
        "cutover_checklist_items",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("checklist_id", sa.String(), nullable=False),
        sa.Column("package_id", sa.String(), nullable=False),
        sa.Column("template_item_id", sa.String(), nullable=True),
        sa.Column("item_code", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("method", sa.String(), nullable=False),
        sa.Column("table_name", sa.String(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("evidence_required", sa.Boolean(), nullable=False),
        sa.Column("evidence_id", sa.String(), nullable=True),
        sa.Column("details_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["checklist_id"], ["cutover_checklists.id"]),
        sa.ForeignKeyConstraint(["package_id"], ["load_plan_packages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "checklist_id",
        "evidence_id",
        "item_code",
        "method",
        "package_id",
        "sort_order",
        "status",
        "table_name",
        "template_item_id",
    ):
        op.create_index(f"ix_cutover_checklist_items_{column}", "cutover_checklist_items", [column])


def downgrade() -> None:
    for column in (
        "template_item_id",
        "table_name",
        "status",
        "sort_order",
        "package_id",
        "method",
        "item_code",
        "evidence_id",
        "checklist_id",
    ):
        op.drop_index(f"ix_cutover_checklist_items_{column}", table_name="cutover_checklist_items")
    op.drop_table("cutover_checklist_items")
    for column in (
        "template_id",
        "status",
        "project_id",
        "profile_id",
        "package_type",
        "package_id",
        "evidence_id",
        "environment_id",
        "created_by",
        "catalog_macro_object_code",
    ):
        op.drop_index(f"ix_cutover_checklists_{column}", table_name="cutover_checklists")
    op.drop_table("cutover_checklists")
    op.drop_index(
        "ix_cutover_checklist_template_items_template_id",
        table_name="cutover_checklist_template_items",
    )
    op.drop_index(
        "ix_cutover_checklist_template_items_sort_order",
        table_name="cutover_checklist_template_items",
    )
    op.drop_index(
        "ix_cutover_checklist_template_items_item_code",
        table_name="cutover_checklist_template_items",
    )
    op.drop_table("cutover_checklist_template_items")
    op.drop_index("ix_cutover_checklist_templates_status", table_name="cutover_checklist_templates")
    op.drop_index("ix_cutover_checklist_templates_code", table_name="cutover_checklist_templates")
    op.drop_table("cutover_checklist_templates")
