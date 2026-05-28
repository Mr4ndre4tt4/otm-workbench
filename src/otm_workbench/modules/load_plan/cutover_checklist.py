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
    LoadPlanZipAnalysis,
)
from otm_workbench.modules.load_plan.packages import parse_json_list, parse_json_object


DEFAULT_TEMPLATE_CODE = "MVP0_STANDARD_CUTOVER"
ALLOWED_ITEM_STATUSES = {"PENDING", "DONE", "BLOCKED", "SKIPPED"}
ALLOWED_ITEM_METHODS = {"CSVUTIL", "REVIEW", "MANUAL", "SYSTEM"}
READY_STATUS = "READY"
BLOCKED_STATUS = "BLOCKED"
NEEDS_REVIEW_STATUS = "NEEDS_REVIEW"
PACKAGE_FAMILY_ORDER = ["AGENTS_REFNUMS", "MASTER_DATA", "RATES", "MISC", "PARAMETER_SET", "UNCLASSIFIED"]
PACKAGE_FAMILY_LABELS = {
    "AGENTS_REFNUMS": "Agents and refnums",
    "MASTER_DATA": "Master data",
    "RATES": "Rates",
    "MISC": "Misc operational setup",
    "PARAMETER_SET": "Parameter set",
    "UNCLASSIFIED": "Unclassified",
}
AGENTS_REFNUM_TABLES = {
    "AGENT",
    "AGENT_ACTION_DETAILS",
    "AGENT_EVENT",
    "AGENT_EVENT_DETAILS",
    "LOCATION_REFNUM",
    "LOCATION_REFNUM_QUAL",
    "ORDER_RELEASE_REFNUM_QUAL",
    "SAVED_CONDITION",
    "SAVED_CONDITION_QUERY",
    "SAVED_QUERY",
    "SAVED_QUERY_ACCESS",
    "SAVED_QUERY_VALUES",
    "SHIPMENT_REFNUM_QUAL",
}
MASTER_DATA_TABLES = {
    "EQUIPMENT_GROUP",
    "EQUIPMENT_GROUP_PROFILE",
    "EQUIPMENT_GROUP_PROFILE_D",
    "ITEM",
    "LOCATION",
    "LOCATION_ACTIVITY_TIME_DEF",
    "LOCATION_ADDRESS",
    "LOCATION_CAPACITY",
    "LOCATION_LOAD_UNLOAD_POINT",
    "PACKAGED_ITEM",
    "REGION",
    "REGION_DETAIL",
    "SHIP_UNIT_SPEC",
    "TI_HI",
}
PARAMETER_SET_TABLES = {"PARAMETER_SET", "PARAMETER_SET_DETAIL"}

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


def domain_name_for_package(package: LoadPlanPackage | None) -> str | None:
    if package is None:
        return None
    if package.domain_name:
        return package.domain_name
    summary = parse_json_object(package.summary_json)
    domain_name = summary.get("domain_name")
    return domain_name if isinstance(domain_name, str) and domain_name else None


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


def checklist_status_counts(db: Session, checklist_id: str) -> dict[str, int]:
    items = (
        db.query(CutoverChecklistItem)
        .filter(CutoverChecklistItem.checklist_id == checklist_id)
        .all()
    )
    counts: dict[str, int] = {}
    for item in items:
        counts[item.status] = counts.get(item.status, 0) + 1
    return dict(sorted(counts.items()))


def refresh_checklist_summary(db: Session, checklist: CutoverChecklist) -> None:
    summary = parse_json_object(checklist.summary_json)
    summary["status_counts"] = checklist_status_counts(db, checklist.id)
    checklist.summary_json = json.dumps(summary, sort_keys=True)
    db.flush()


def update_checklist_item(
    db: Session,
    *,
    item: CutoverChecklistItem,
    status: str | None,
    method: str | None,
    evidence_id: str | None,
    updated_by: str,
) -> CutoverChecklist:
    if status is not None and status not in ALLOWED_ITEM_STATUSES:
        raise ValueError("Invalid cutover checklist item status.")
    if method is not None and method not in ALLOWED_ITEM_METHODS:
        raise ValueError("Invalid cutover checklist item method.")

    final_status = status or item.status
    final_evidence_id = evidence_id if evidence_id is not None else item.evidence_id
    if final_status == "DONE" and item.evidence_required and not final_evidence_id:
        raise ValueError("Evidence is required before marking this checklist item as DONE.")

    evidence = None
    if evidence_id:
        evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if evidence is None:
            raise LookupError("Evidence not found.")
        if not evidence.client_safe:
            raise ValueError("Evidence must be client-safe before linking it to a cutover checklist item.")

    previous_status = item.status
    previous_method = item.method
    if status is not None:
        item.status = status
    if method is not None:
        item.method = method
    if evidence_id is not None:
        item.evidence_id = evidence_id
    db.flush()

    checklist = db.query(CutoverChecklist).filter(CutoverChecklist.id == item.checklist_id).one()
    refresh_checklist_summary(db, checklist)
    summary = parse_json_object(checklist.summary_json)
    audit_payload = {
        "checklist_id": checklist.id,
        "package_id": checklist.package_id,
        "item_id": item.id,
        "item_code": item.item_code,
        "table_name": item.table_name,
        "previous_status": previous_status,
        "status": item.status,
        "previous_method": previous_method,
        "method": item.method,
        "evidence_id": item.evidence_id,
        "status_counts": summary.get("status_counts", {}),
    }
    if checklist.catalog_macro_object_code:
        audit_payload["catalog_macro_object_code"] = checklist.catalog_macro_object_code
    db.add(
        AuditLog(
            actor_user_id=updated_by,
            action="load_plan.cutover_checklist_item.update",
            target_type="cutover_checklist_item",
            target_id=item.id,
            metadata_json=json.dumps(audit_payload, sort_keys=True),
        )
    )
    db.add(
        DomainEvent(
            event_type="load_plan.cutover_checklist_item.updated",
            source_module="load_plan",
            project_id=checklist.project_id,
            aggregate_type="cutover_checklist_item",
            aggregate_id=item.id,
            payload_json=json.dumps(audit_payload, sort_keys=True),
            status="PENDING",
        )
    )
    db.commit()
    db.refresh(checklist)
    return checklist


def readiness_blocker(item: CutoverChecklistItem, code: str, severity: str, message: str) -> dict[str, object]:
    return {
        "code": code,
        "severity": severity,
        "item_id": item.id,
        "item_code": item.item_code,
        "table_name": item.table_name,
        "message": message,
        "details": {
            "status": item.status,
            "method": item.method,
            "evidence_required": item.evidence_required,
        },
    }


def package_family_for_table(table_name: str | None) -> str:
    if not table_name:
        return "UNCLASSIFIED"
    normalized = table_name.upper()
    if normalized in AGENTS_REFNUM_TABLES:
        return "AGENTS_REFNUMS"
    if normalized in PARAMETER_SET_TABLES or normalized.startswith("PARAMETER_"):
        return "PARAMETER_SET"
    if normalized.startswith("RATE_") or normalized in {
        "ACCESSORIAL_CODE",
        "ACCESSORIAL_COST",
        "ACCESSORIAL_COST_UNIT_BREAK",
        "X_LANE",
    }:
        return "RATES"
    if normalized in MASTER_DATA_TABLES or normalized.startswith("GEO_"):
        return "MASTER_DATA"
    return "MISC"


def package_family_readiness(
    items: list[CutoverChecklistItem],
    blockers: list[dict[str, object]],
) -> list[dict[str, object]]:
    families: dict[str, dict[str, object]] = {}

    def ensure_family(family_code: str) -> dict[str, object]:
        if family_code not in families:
            families[family_code] = {
                "family_code": family_code,
                "label": PACKAGE_FAMILY_LABELS.get(family_code, family_code.replace("_", " ").title()),
                "status": READY_STATUS,
                "table_count": 0,
                "item_count": 0,
                "blocker_count": 0,
                "error_count": 0,
                "warning_count": 0,
            }
        return families[family_code]

    for item in items:
        if not item.table_name:
            continue
        family = ensure_family(package_family_for_table(item.table_name))
        family["item_count"] = int(family["item_count"]) + 1
        family["table_count"] = int(family["table_count"]) + 1

    for blocker in blockers:
        family = ensure_family(package_family_for_table(blocker.get("table_name")))
        family["blocker_count"] = int(family["blocker_count"]) + 1
        if blocker.get("severity") == "ERROR":
            family["error_count"] = int(family["error_count"]) + 1
        elif blocker.get("severity") == "WARNING":
            family["warning_count"] = int(family["warning_count"]) + 1

    for family in families.values():
        if int(family["error_count"]):
            family["status"] = BLOCKED_STATUS
        elif int(family["warning_count"]):
            family["status"] = NEEDS_REVIEW_STATUS
        else:
            family["status"] = READY_STATUS

    return [
        families[family_code]
        for family_code in PACKAGE_FAMILY_ORDER
        if family_code in families
    ]


def latest_zip_analysis_for_package(db: Session, package_id: str) -> LoadPlanZipAnalysis | None:
    return (
        db.query(LoadPlanZipAnalysis)
        .filter(LoadPlanZipAnalysis.package_id == package_id)
        .order_by(LoadPlanZipAnalysis.analyzed_at.desc(), LoadPlanZipAnalysis.created_at.desc())
        .first()
    )


def zip_analysis_readiness_blockers(analysis: LoadPlanZipAnalysis) -> list[dict[str, object]]:
    blockers: list[dict[str, object]] = []
    for finding_item in parse_json_list(analysis.findings_json):
        severity = str(finding_item.get("severity", "WARNING")).upper()
        if severity not in {"ERROR", "WARNING"}:
            continue
        source_code = str(finding_item.get("code", "ZIP_ANALYSIS_FINDING"))
        details = dict(finding_item.get("details", {})) if isinstance(finding_item.get("details"), dict) else {}
        details["source_code"] = source_code
        details["zip_analysis_id"] = analysis.id
        blockers.append(
            {
                "code": "ZIP_ANALYSIS_ERROR" if severity == "ERROR" else "ZIP_ANALYSIS_WARNING",
                "severity": severity,
                "item_id": None,
                "item_code": None,
                "table_name": finding_item.get("table_name"),
                "file_name": finding_item.get("file_name"),
                "message": str(finding_item.get("message", "ZIP analysis finding requires review.")),
                "details": details,
            }
        )
    return blockers


def checklist_readiness_payload(db: Session, checklist: CutoverChecklist) -> dict[str, object]:
    items = (
        db.query(CutoverChecklistItem)
        .filter(CutoverChecklistItem.checklist_id == checklist.id)
        .order_by(CutoverChecklistItem.sort_order, CutoverChecklistItem.created_at)
        .all()
    )
    blockers: list[dict[str, object]] = []
    for item in items:
        if item.status == "BLOCKED":
            blockers.append(
                readiness_blocker(item, "ITEM_BLOCKED", "ERROR", "Checklist item is marked as BLOCKED.")
            )
        elif item.status == "PENDING" and item.evidence_required:
            blockers.append(
                readiness_blocker(
                    item,
                    "REQUIRED_ITEM_PENDING",
                    "ERROR",
                    "Required checklist item is still PENDING.",
                )
            )
        elif item.status == "DONE" and item.evidence_required and not item.evidence_id:
            blockers.append(
                readiness_blocker(
                    item,
                    "DONE_ITEM_MISSING_EVIDENCE",
                    "ERROR",
                    "Required checklist item is DONE but has no evidence linked.",
                )
            )
        elif item.status == "SKIPPED":
            blockers.append(
                readiness_blocker(item, "ITEM_SKIPPED", "WARNING", "Checklist item was skipped and needs review.")
            )

    latest_zip_analysis = latest_zip_analysis_for_package(db, checklist.package_id)
    zip_analysis_summary: dict[str, object] = {}
    if latest_zip_analysis is not None:
        zip_analysis_summary = parse_json_object(latest_zip_analysis.summary_json)
        blockers.extend(zip_analysis_readiness_blockers(latest_zip_analysis))

    status_counts = checklist_status_counts(db, checklist.id)
    error_count = sum(1 for blocker in blockers if blocker["severity"] == "ERROR")
    warning_count = sum(1 for blocker in blockers if blocker["severity"] == "WARNING")
    package_families = package_family_readiness(items, blockers)
    status = READY_STATUS
    if error_count:
        status = BLOCKED_STATUS
    elif warning_count:
        status = NEEDS_REVIEW_STATUS

    summary = parse_json_object(checklist.summary_json)
    readiness_summary = {
        "ready": status == READY_STATUS,
        "item_count": len(items),
        "done_count": status_counts.get("DONE", 0),
        "pending_count": status_counts.get("PENDING", 0),
        "blocked_count": status_counts.get("BLOCKED", 0),
        "skipped_count": status_counts.get("SKIPPED", 0),
        "missing_evidence_count": sum(
            1 for item in items if item.status == "DONE" and item.evidence_required and not item.evidence_id
        ),
        "blocker_count": len(blockers),
        "error_count": error_count,
        "warning_count": warning_count,
        "status_counts": status_counts,
        "package_families": package_families,
    }
    if latest_zip_analysis is not None:
        readiness_summary.update(
            {
                "latest_zip_analysis_id": latest_zip_analysis.id,
                "zip_analysis_finding_count": int(zip_analysis_summary.get("finding_count", 0)),
                "zip_analysis_error_count": int(zip_analysis_summary.get("error_count", 0)),
                "zip_analysis_warning_count": int(zip_analysis_summary.get("warning_count", 0)),
            }
        )
    for key in ("catalog_macro_object_code", "catalog_load_plan_path"):
        if summary.get(key):
            readiness_summary[key] = summary[key]

    return {
        "checklist_id": checklist.id,
        "package_id": checklist.package_id,
        "status": status,
        "summary": readiness_summary,
        "blockers": blockers,
    }


def generate_checklist_readiness(
    db: Session,
    *,
    checklist: CutoverChecklist,
    generated_by: str,
) -> dict[str, object]:
    package = db.query(LoadPlanPackage).filter(LoadPlanPackage.id == checklist.package_id).first()
    domain_name = domain_name_for_package(package)
    payload = checklist_readiness_payload(db, checklist)
    summary = payload["summary"]
    evidence_summary = {
        "source_entity_type": "cutover_checklist",
        "source_entity_id": checklist.id,
        "package_id": checklist.package_id,
        "status": payload["status"],
        "item_count": summary["item_count"],
        "blocker_count": summary["blocker_count"],
        "error_count": summary["error_count"],
        "warning_count": summary["warning_count"],
    }
    if domain_name:
        evidence_summary["domain_name"] = domain_name
    for key in ("catalog_macro_object_code", "catalog_load_plan_path"):
        if summary.get(key):
            evidence_summary[key] = summary[key]
    evidence = Evidence(
        project_id=checklist.project_id,
        profile_id=checklist.profile_id,
        environment_id=checklist.environment_id,
        domain_name=domain_name,
        visibility="PROJECT",
        source_module="load_plan",
        evidence_type="cutover_checklist_readiness",
        summary_json=json.dumps(evidence_summary, sort_keys=True),
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db.add(evidence)
    db.flush()
    payload["evidence_id"] = evidence.id

    audit_payload = dict(evidence_summary)
    audit_payload["evidence_id"] = evidence.id
    audit_payload["project_id"] = checklist.project_id
    audit_payload["profile_id"] = checklist.profile_id
    audit_payload["environment_id"] = checklist.environment_id
    db.add(
        AuditLog(
            actor_user_id=generated_by,
            action="load_plan.cutover_checklist.readiness",
            target_type="cutover_checklist",
            target_id=checklist.id,
            metadata_json=json.dumps(audit_payload, sort_keys=True),
        )
    )
    db.add(
        DomainEvent(
            event_type="load_plan.cutover_checklist.readiness.generated",
            source_module="load_plan",
            project_id=checklist.project_id,
            aggregate_type="cutover_checklist",
            aggregate_id=checklist.id,
            payload_json=json.dumps(audit_payload, sort_keys=True),
            status="PENDING",
        )
    )
    db.commit()
    return payload


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
    domain_name = domain_name_for_package(package)
    if domain_name:
        evidence_summary["domain_name"] = domain_name
    for key in ("catalog_macro_object_code", "catalog_load_plan_path"):
        if summary.get(key):
            evidence_summary[key] = summary[key]
    evidence = Evidence(
        project_id=package.project_id,
        profile_id=package.profile_id,
        environment_id=package.environment_id,
        domain_name=domain_name,
        visibility="PROJECT",
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
        "project_id": package.project_id,
        "profile_id": package.profile_id,
        "environment_id": package.environment_id,
    }
    if domain_name:
        audit_payload["domain_name"] = domain_name
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
