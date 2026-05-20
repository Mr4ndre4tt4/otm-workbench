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


def seed_modules(db: Session) -> None:
    modules = [
        Module(
            id="master_data",
            display_name="Data Factory",
            route_base="/master-data",
            status="ACTIVE",
            group_key="build",
            group_label="Build",
            icon_key="database",
            sort_order=210,
            surface_type="module",
            description="Create and validate reusable OTM master data load templates.",
        ),
        Module(
            id="home",
            display_name="Project Cockpit",
            route_base="/home",
            status="ACTIVE",
            group_key="cockpit",
            group_label="Cockpit",
            icon_key="layout-dashboard",
            sort_order=100,
            surface_type="workspace",
            description="Project cockpit and operational overview.",
        ),
        Module(
            id="evidence",
            display_name="Evidence Hub",
            route_base="/evidence",
            status="PLANNED",
            group_key="cockpit",
            group_label="Cockpit",
            icon_key="archive",
            sort_order=120,
            surface_type="workspace",
            description="Browse client-safe evidence, manifests and linked artifacts.",
        ),
        Module(
            id="rates",
            display_name="Rates Studio",
            route_base="/rates",
            status="PLANNED",
            group_key="build",
            group_label="Build",
            icon_key="badge-dollar-sign",
            sort_order=220,
            surface_type="module",
            description="Prepare, validate, approve and export OTM rates packages.",
            required_capability="rates.reference.view",
        ),
        Module(
            id="catalog",
            display_name="OTM Catalog Core",
            route_base="/catalog",
            status="ACTIVE",
            group_key="govern",
            group_label="Govern",
            icon_key="book-open",
            sort_order=310,
            surface_type="reference",
            description="Explore OTM Data Dictionary objects, columns and load plans.",
        ),
        Module(
            id="load_plan",
            display_name="Load Plan",
            route_base="/load-plan",
            status="PLANNED",
            group_key="govern",
            group_label="Govern",
            icon_key="list-checks",
            sort_order=320,
            surface_type="module",
            description="Create load packages, cutover readiness and CSVUTIL handoff assets.",
        ),
        Module(
            id="assets",
            display_name="Assets Library",
            route_base="/assets",
            status="ACTIVE",
            group_key="govern",
            group_label="Govern",
            icon_key="folder-open",
            sort_order=330,
            surface_type="library",
            description="Manage reusable files, templates and module-linked assets.",
        ),
        Module(
            id="order_release_generator",
            display_name="Order Release Generator",
            route_base="/order-release-generator",
            status="ACTIVE",
            group_key="build",
            group_label="Build",
            icon_key="file-plus-2",
            sort_order=240,
            surface_type="module",
            description="Generate synthetic Order Release XML payloads for OTM tests.",
        ),
        Module(
            id="integration_mapping",
            display_name="Integration Mapping Studio",
            route_base="/integration-mapping",
            status="ACTIVE",
            group_key="build",
            group_label="Build",
            icon_key="git-branch",
            sort_order=250,
            surface_type="module",
            description="Model source-to-target payload mappings and generate integration specs.",
        ),
        Module(
            id="admin",
            display_name="Admin Console",
            route_base="/admin",
            status="PLANNED",
            group_key="admin",
            group_label="Admin",
            icon_key="settings",
            sort_order=410,
            surface_type="admin",
            description="Manage project, profile, environment and administrative settings.",
            admin_only=True,
        ),
        Module(
            id="dev_tools",
            display_name="Developer Tools",
            route_base="/dev-tools",
            status="PLANNED",
            group_key="admin",
            group_label="Admin",
            icon_key="terminal",
            sort_order=490,
            surface_type="developer",
            description="Developer-only diagnostics and internal tools.",
            is_primary=False,
            dev_only=True,
            feature_flag="dev_tools",
        ),
    ]
    for module in modules:
        if not db.get(Module, module.id):
            db.add(module)
    db.commit()


def flag_enabled(db: Session, name: str | None) -> bool:
    if not name:
        return True
    flag = db.query(FeatureFlag).filter(FeatureFlag.name == name).first()
    return bool(flag and flag.enabled)


def registered_modules(db: Session) -> list[Module]:
    seed_modules(db)
    order = [
        "home",
        "evidence",
        "master_data",
        "rates",
        "order_release_generator",
        "integration_mapping",
        "catalog",
        "load_plan",
        "assets",
        "admin",
        "dev_tools",
    ]
    modules_by_id = {module.id: module for module in db.query(Module).all()}
    return [modules_by_id[module_id] for module_id in order if module_id in modules_by_id]


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


def navigation_items(db: Session, user: User) -> list[dict[str, object]]:
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
                "path": module.route_base,
                "status": module.status,
                "group_key": module.group_key,
                "group_label": module.group_label,
                "icon_key": module.icon_key,
                "sort_order": module.sort_order,
                "surface_type": module.surface_type,
                "description": module.description,
                "is_primary": module.is_primary,
            }
        )
    return items
