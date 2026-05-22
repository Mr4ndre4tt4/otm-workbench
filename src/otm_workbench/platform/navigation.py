import json

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from otm_workbench.models import (
    ActiveContext,
    Capability,
    FeatureFlag,
    Module,
    Role,
    RoleCapability,
    User,
    UserProjectRole,
)

ICONLY_FILE_KEY = "8h6mUDOqSXent0hqlSY7k7"


def icon_ref(icon_name: str, page: str) -> str:
    return json.dumps(
        {
            "figma_file_key": ICONLY_FILE_KEY,
            "figma_page": page,
            "figma_node_name": f"Iconly/Regular/Broken/{icon_name}",
        }
    )


def seed_modules(db: Session) -> None:
    modules = [
        Module(
            id="master_data",
            display_name="Data Factory",
            route_base="/master-data",
            status="ACTIVE",
            label_key="module.master_data.label",
            description="Template-driven master data preparation and OTM CSV package generation.",
            icon_key="master_data",
            icon_name="Paper",
            sort_order=10,
        ),
        Module(
            id="home",
            display_name="Project Cockpit",
            route_base="/home",
            status="ACTIVE",
            label_key="module.home.label",
            description="Project-level operational overview for active context, jobs, artifacts, and evidence.",
            icon_key="home",
            icon_name="Home",
            sort_order=20,
        ),
        Module(
            id="evidence",
            display_name="Evidence Hub",
            route_base="/evidence",
            status="PLANNED",
            label_key="module.evidence.label",
            description="Client-safe evidence, manifests, artifacts, and implementation audit trail.",
            icon_key="evidence",
            icon_name="Shield Done",
            sort_order=30,
        ),
        Module(
            id="rates",
            display_name="Rates Studio",
            route_base="/rates",
            status="PLANNED",
            label_key="module.rates.label",
            description="Rate reference catalog, validation, lifecycle, and CSVUTIL export workflow.",
            icon_key="rates",
            icon_name="Chart",
            sort_order=40,
            required_capability="rates.reference.view",
        ),
        Module(
            id="catalog",
            display_name="OTM Catalog Core",
            route_base="/catalog",
            status="ACTIVE",
            label_key="module.catalog.label",
            description="Canonical OTM catalog foundation for macro objects, data dictionary, and load plans.",
            icon_key="catalog",
            icon_name="Folder",
            sort_order=50,
        ),
        Module(
            id="load_plan",
            display_name="Load Plan",
            route_base="/load-plan",
            status="PLANNED",
            label_key="module.load_plan.label",
            description="Cutover load plan packages, readiness review, CSVUTIL builds, and handoff controls.",
            icon_key="load_plan",
            icon_name="Calendar",
            sort_order=60,
        ),
        Module(
            id="assets",
            display_name="Assets Library",
            route_base="/assets",
            status="ACTIVE",
            label_key="module.assets.label",
            description="Versioned files, module links, and governed implementation assets.",
            icon_key="assets",
            icon_name="Image",
            sort_order=70,
        ),
        Module(
            id="order_release_generator",
            display_name="Order Release Generator",
            route_base="/order-release-generator",
            status="ACTIVE",
            label_key="module.order_release_generator.label",
            description="Order release template, batch, XML artifact, and guarded OTM submit workflow.",
            icon_key="order_release_generator",
            icon_name="Paper Upload",
            sort_order=80,
        ),
        Module(
            id="integration_mapping",
            display_name="Integration Mapping Studio",
            route_base="/integration-mapping",
            status="ACTIVE",
            label_key="module.integration_mapping.label",
            description="Integration definition authoring, payload schemas, mappings, joins, loops, and previews.",
            icon_key="integration_mapping",
            icon_name="Swap",
            sort_order=90,
        ),
        Module(
            id="admin",
            display_name="Admin Console",
            route_base="/admin",
            status="PLANNED",
            label_key="module.admin.label",
            description="Platform administration for setup, features, jobs, and audit visibility.",
            icon_key="admin",
            icon_name="Setting",
            sort_order=100,
            admin_only=True,
        ),
        Module(
            id="dev_tools",
            display_name="Developer Tools",
            route_base="/dev-tools",
            status="PLANNED",
            label_key="module.dev_tools.label",
            description="Internal developer diagnostics and platform tooling.",
            icon_key="dev_tools",
            icon_name="Work",
            sort_order=110,
            dev_only=True,
            feature_flag="dev_tools",
        ),
    ]
    for module in modules:
        module.icon_light_ref_json = icon_ref(module.icon_name, "Library | Light")
        module.icon_dark_ref_json = icon_ref(module.icon_name, "Library | Dark")
        existing = db.get(Module, module.id)
        if not existing:
            db.add(module)
            continue
        for field in (
            "display_name",
            "route_base",
            "status",
            "label_key",
            "description",
            "icon_key",
            "icon_family",
            "icon_variant",
            "icon_style",
            "icon_name",
            "icon_light_ref_json",
            "icon_dark_ref_json",
            "sort_order",
            "required_capability",
            "feature_flag",
            "admin_only",
            "dev_only",
        ):
            setattr(existing, field, getattr(module, field))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()


def flag_enabled(db: Session, name: str | None) -> bool:
    if not name:
        return True
    flag = db.query(FeatureFlag).filter(FeatureFlag.name == name).first()
    return bool(flag and flag.enabled)


def registered_modules(db: Session) -> list[Module]:
    seed_modules(db)
    return db.query(Module).order_by(Module.sort_order, Module.id).all()


def effective_capability_names(db: Session, user: User) -> set[str]:
    if user.is_admin:
        return {"*"}
    active_context = db.query(ActiveContext).filter(ActiveContext.user_id == user.id).first()
    if not active_context or not active_context.project_id:
        return set()
    rows = (
        db.query(Capability.name)
        .join(RoleCapability, RoleCapability.capability_id == Capability.id)
        .join(Role, Role.id == RoleCapability.role_id)
        .join(UserProjectRole, UserProjectRole.role_id == Role.id)
        .filter(
            UserProjectRole.user_id == user.id,
            UserProjectRole.project_id == active_context.project_id,
        )
        .all()
    )
    return {row[0] for row in rows}


def has_required_capability(capabilities: set[str], required_capability: str | None) -> bool:
    return not required_capability or "*" in capabilities or required_capability in capabilities


def navigation_items(db: Session, user: User) -> list[dict[str, str]]:
    items = []
    capabilities = effective_capability_names(db, user)
    for module in registered_modules(db):
        if module.admin_only and not user.is_admin:
            continue
        if module.dev_only and (not user.is_admin or not flag_enabled(db, module.feature_flag)):
            continue
        if not flag_enabled(db, module.feature_flag):
            continue
        if not has_required_capability(capabilities, module.required_capability):
            continue
        items.append(
            {
                "id": module.id,
                "label": module.display_name,
                "label_key": module.label_key or f"module.{module.id}.label",
                "description": module.description,
                "path": module.route_base,
                "status": module.status,
                "icon_key": module.icon_key,
                "icon_family": module.icon_family,
                "icon_variant": module.icon_variant,
                "icon_style": module.icon_style,
                "icon_name": module.icon_name,
                "icon_light_ref": json.loads(module.icon_light_ref_json or "{}"),
                "icon_dark_ref": json.loads(module.icon_dark_ref_json or "{}"),
            }
        )
    return items
