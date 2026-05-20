import json

from sqlalchemy.orm import Session

from otm_workbench.models import (
    AuditLog,
    CutoverChecklist,
    CutoverChecklistItem,
    CutoverChecklistTemplate,
    CutoverChecklistTemplateItem,
    DomainEvent,
    Evidence,
    LoadPlanPackage,
)
from otm_workbench.modules.load_plan.packages import parse_json_list, parse_json_object


DEFAULT_TEMPLATE_CODE = "MVP0_STANDARD_CUTOVER"

DEFAULT_TEMPLATE_ITEMS = [
    {
        "item_code": "PACKAGE_REGISTERED",
        "title": "Confirm package registration",
        "description": "Confirms that the source package was registered in Load Plan.",
        "default_method": "SYSTEM",
        "sort_order": 10,
        "required_evidence_type": "load_plan_package_intake",
    },
    {
        "item_code": "SEQUENCE_REVIEW",
        "title": "Review load sequence",
        "description": "Confirms that the package sequence is reviewed before cutover execution.",
        "default_method": "REVIEW",
        "sort_order": 20,
        "required_evidence_type": "load_plan_sequence_snapshot",
    },
    {
        "item_code": "TABLE_READY",
        "title": "Confirm technical table readiness",
        "description": "Generated once for each technical table in the package load sequence.",
        "default_method": "CSVUTIL",
        "sort_order": 100,
        "required_evidence_type": "cutover_table_readiness",
    },
]


def ensure_default_template(db: Session) -> CutoverChecklistTemplate:
    template = (
        db.query(CutoverChecklistTemplate)
        .filter(CutoverChecklistTemplate.code == DEFAULT_TEMPLATE_CODE)
        .first()
    )
    if template is None:
        template = CutoverChecklistTemplate(
            code=DEFAULT_TEMPLATE_CODE,
            name="MVP0 Standard Cutover Checklist",
            version=1,
            status="PUBLISHED",
            description="Backend-first seed for Load Plan cutover governance.",
            system_seeded=True,
        )
        db.add(template)
        db.flush()

    existing_codes = {
        item.item_code
        for item in db.query(CutoverChecklistTemplateItem)
        .filter(CutoverChecklistTemplateItem.template_id == template.id)
        .all()
    }
    for item in DEFAULT_TEMPLATE_ITEMS:
        if item["item_code"] in existing_codes:
            continue
        db.add(
            CutoverChecklistTemplateItem(
                template_id=template.id,
                item_code=str(item["item_code"]),
                title=str(item["title"]),
                description=str(item["description"]),
                default_method=str(item["default_method"]),
                applies_to_package_type="*",
                required_evidence_type=str(item["required_evidence_type"]),
                sort_order=int(item["sort_order"]),
                is_required=True,
            )
        )
    db.flush()
    return template


def template_items(db: Session, template_id: str) -> list[CutoverChecklistTemplateItem]:
    return (
        db.query(CutoverChecklistTemplateItem)
        .filter(CutoverChecklistTemplateItem.template_id == template_id)
        .order_by(CutoverChecklistTemplateItem.sort_order, CutoverChecklistTemplateItem.item_code)
        .all()
    )


def serialize_template(template: CutoverChecklistTemplate, items: list[CutoverChecklistTemplateItem]) -> dict[str, object]:
    return {
        "id": template.id,
        "code": template.code,
        "name": template.name,
        "version": template.version,
        "status": template.status,
        "description": template.description,
        "system_seeded": template.system_seeded,
        "items": [
            {
                "id": item.id,
                "item_code": item.item_code,
                "title": item.title,
                "description": item.description,
                "default_method": item.default_method,
                "applies_to_package_type": item.applies_to_package_type,
                "required_evidence_type": item.required_evidence_type,
                "sort_order": item.sort_order,
                "is_required": item.is_required,
            }
            for item in items
        ],
    }


def list_seeded_templates(db: Session) -> list[dict[str, object]]:
    template = ensure_default_template(db)
    db.commit()
    db.refresh(template)
    return [serialize_template(template, template_items(db, template.id))]


def existing_checklist_for_package(db: Session, package_id: str, template_id: str) -> CutoverChecklist | None:
    return (
        db.query(CutoverChecklist)
        .filter(CutoverChecklist.package_id == package_id)
        .filter(CutoverChecklist.template_id == template_id)
        .order_by(CutoverChecklist.created_at.desc())
        .first()
    )


def method_for_package(package: LoadPlanPackage) -> str:
    if package.package_type.endswith("_csv_zip"):
        return "CSVUTIL"
    return "REVIEW"


def build_summary(package: LoadPlanPackage, *, item_count: int, table_item_count: int) -> dict[str, object]:
    package_summary = parse_json_object(package.summary_json)
    catalog_context = {
        key: package_summary[key]
        for key in ("catalog_macro_object_code", "catalog_load_plan_path")
        if package_summary.get(key)
    }
    package_item_count = len(parse_json_list(package.load_sequence_json))
    return {
        "source_module": package.source_module,
        "package_type": package.package_type,
        "package_status": package.status,
        "item_count": item_count,
        "package_item_count": package_item_count,
        "table_item_count": table_item_count,
        **catalog_context,
    }


def serialize_checklist_item(item: CutoverChecklistItem) -> dict[str, object]:
    return {
        "id": item.id,
        "checklist_id": item.checklist_id,
        "package_id": item.package_id,
        "template_item_id": item.template_item_id,
        "item_code": item.item_code,
        "title": item.title,
        "status": item.status,
        "method": item.method,
        "table_name": item.table_name,
        "sort_order": item.sort_order,
        "evidence_required": item.evidence_required,
        "evidence_id": item.evidence_id,
        "details": parse_json_object(item.details_json),
    }


def serialize_checklist(db: Session, checklist: CutoverChecklist) -> dict[str, object]:
    template = (
        db.query(CutoverChecklistTemplate)
        .filter(CutoverChecklistTemplate.id == checklist.template_id)
        .first()
    )
    items = (
        db.query(CutoverChecklistItem)
        .filter(CutoverChecklistItem.checklist_id == checklist.id)
        .order_by(CutoverChecklistItem.sort_order, CutoverChecklistItem.created_at)
        .all()
    )
    return {
        "id": checklist.id,
        "project_id": checklist.project_id,
        "environment_id": checklist.environment_id,
        "profile_id": checklist.profile_id,
        "template_id": checklist.template_id,
        "template_code": template.code if template else None,
        "package_id": checklist.package_id,
        "status": checklist.status,
        "package_type": checklist.package_type,
        "catalog_macro_object_code": checklist.catalog_macro_object_code,
        "summary": parse_json_object(checklist.summary_json),
        "evidence_id": checklist.evidence_id,
        "created_by": checklist.created_by,
        "items": [serialize_checklist_item(item) for item in items],
    }


def create_checklist_from_package(
    db: Session,
    *,
    package: LoadPlanPackage,
    created_by: str,
) -> CutoverChecklist:
    template = ensure_default_template(db)
    existing = existing_checklist_for_package(db, package.id, template.id)
    if existing:
        return existing

    package_summary = parse_json_object(package.summary_json)
    catalog_macro_object_code = package_summary.get("catalog_macro_object_code")
    checklist = CutoverChecklist(
        project_id=package.project_id,
        environment_id=package.environment_id,
        profile_id=package.profile_id,
        template_id=template.id,
        package_id=package.id,
        status="DRAFT",
        package_type=package.package_type,
        catalog_macro_object_code=catalog_macro_object_code if isinstance(catalog_macro_object_code, str) else None,
        created_by=created_by,
    )
    db.add(checklist)
    db.flush()

    items = template_items(db, template.id)
    package_method = method_for_package(package)
    created_items: list[CutoverChecklistItem] = []
    for template_item in items:
        if template_item.item_code == "TABLE_READY":
            for sequence_item in parse_json_list(package.load_sequence_json):
                table_name = sequence_item.get("table_name")
                if not isinstance(table_name, str) or not table_name:
                    continue
                details = {
                    "position": sequence_item.get("position"),
                    "row_count": sequence_item.get("row_count"),
                    "requirement_level": sequence_item.get("requirement_level"),
                }
                created_items.append(
                    CutoverChecklistItem(
                        checklist_id=checklist.id,
                        package_id=package.id,
                        template_item_id=template_item.id,
                        item_code=template_item.item_code,
                        title=f"Confirm {table_name} readiness",
                        status="PENDING",
                        method=package_method,
                        table_name=table_name,
                        sort_order=template_item.sort_order + int(sequence_item.get("position") or 0),
                        evidence_required=template_item.is_required,
                        details_json=json.dumps(details, sort_keys=True),
                    )
                )
        else:
            created_items.append(
                CutoverChecklistItem(
                    checklist_id=checklist.id,
                    package_id=package.id,
                    template_item_id=template_item.id,
                    item_code=template_item.item_code,
                    title=template_item.title,
                    status="PENDING",
                    method=template_item.default_method,
                    table_name=None,
                    sort_order=template_item.sort_order,
                    evidence_required=template_item.is_required,
                    details_json=json.dumps({"required_evidence_type": template_item.required_evidence_type}, sort_keys=True),
                )
            )
    for item in created_items:
        db.add(item)
    db.flush()

    table_item_count = sum(1 for item in created_items if item.item_code == "TABLE_READY")
    summary = build_summary(package, item_count=len(created_items), table_item_count=table_item_count)
    checklist.summary_json = json.dumps(summary, sort_keys=True)

    evidence_summary = {
        "source_entity_type": "cutover_checklist",
        "source_entity_id": checklist.id,
        "package_id": package.id,
        "template_code": template.code,
        "status": checklist.status,
        "item_count": summary["item_count"],
        "table_item_count": summary["table_item_count"],
        "package_type": package.package_type,
    }
    for key in ("catalog_macro_object_code", "catalog_load_plan_path"):
        if summary.get(key):
            evidence_summary[key] = summary[key]
    evidence = Evidence(
        project_id=package.project_id,
        source_module="load_plan",
        evidence_type="cutover_checklist_created",
        summary_json=json.dumps(evidence_summary, sort_keys=True),
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db.add(evidence)
    db.flush()
    checklist.evidence_id = evidence.id

    audit_payload = {
        "package_id": package.id,
        "template_code": template.code,
        "evidence_id": evidence.id,
        "item_count": summary["item_count"],
        "table_item_count": summary["table_item_count"],
    }
    for key in ("catalog_macro_object_code", "catalog_load_plan_path"):
        if summary.get(key):
            audit_payload[key] = summary[key]
    db.add(
        AuditLog(
            actor_user_id=created_by,
            action="load_plan.cutover_checklist.create_from_package",
            target_type="cutover_checklist",
            target_id=checklist.id,
            metadata_json=json.dumps(audit_payload, sort_keys=True),
        )
    )
    db.add(
        DomainEvent(
            event_type="load_plan.cutover_checklist.created",
            source_module="load_plan",
            project_id=package.project_id,
            aggregate_type="cutover_checklist",
            aggregate_id=checklist.id,
            payload_json=json.dumps(audit_payload, sort_keys=True),
            status="PENDING",
        )
    )
    db.commit()
    db.refresh(checklist)
    return checklist
