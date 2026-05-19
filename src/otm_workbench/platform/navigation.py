from sqlalchemy.orm import Session

from otm_workbench.models import FeatureFlag, Module, User


def seed_modules(db: Session) -> None:
    modules = [
        Module(
            id="master_data",
            display_name="Data Factory",
            route_base="/master-data",
            status="PLANNED",
        ),
        Module(id="home", display_name="Project Cockpit", route_base="/home", status="ACTIVE"),
        Module(
            id="evidence",
            display_name="Evidence Hub",
            route_base="/evidence",
            status="PLANNED",
        ),
        Module(
            id="rates",
            display_name="Rates Studio",
            route_base="/rates",
            status="PLANNED",
            required_capability="rates.reference.view",
        ),
        Module(
            id="catalog",
            display_name="OTM Catalog Core",
            route_base="/catalog",
            status="ACTIVE",
        ),
        Module(
            id="load_plan",
            display_name="Load Plan",
            route_base="/load-plan",
            status="PLANNED",
        ),
        Module(
            id="admin",
            display_name="Admin Console",
            route_base="/admin",
            status="PLANNED",
            admin_only=True,
        ),
        Module(
            id="dev_tools",
            display_name="Developer Tools",
            route_base="/dev-tools",
            status="PLANNED",
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
    order = ["master_data", "home", "evidence", "catalog", "rates", "load_plan", "admin", "dev_tools"]
    modules_by_id = {module.id: module for module in db.query(Module).all()}
    return [modules_by_id[module_id] for module_id in order if module_id in modules_by_id]


def navigation_items(db: Session, user: User) -> list[dict[str, str]]:
    items = []
    for module in registered_modules(db):
        if module.admin_only and not user.is_admin:
            continue
        if module.dev_only and (not user.is_admin or not flag_enabled(db, module.feature_flag)):
            continue
        if not flag_enabled(db, module.feature_flag):
            continue
        items.append(
            {
                "id": module.id,
                "label": module.display_name,
                "path": module.route_base,
                "status": module.status,
            }
        )
    return items
