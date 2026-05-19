import json

from sqlalchemy.orm import Session

from otm_workbench.models import (
    AuditLog,
    DomainEvent,
    Evidence,
    LoadPlanPackage,
    LoadPlanReviewDecision,
    LoadPlanReviewItem,
    LoadPlanZipAnalysis,
    utcnow,
)
from otm_workbench.modules.load_plan.packages import parse_json_list, parse_json_object


SOURCE_TYPE = "zip_analysis_finding"
PENDING_STATUS = "PENDING_REVIEW"
ALLOWED_DECISION_STATUSES = {
    "CONFIRMED",
    "REJECTED",
    "NEEDS_MANUAL_ACTION",
    "EXCLUDED_FROM_CUTOVER",
}

CATEGORY_BY_CODE = {
    "ZIP_MANIFEST_MISSING": "PACKAGE",
    "ZIP_CSV_MISSING": "STRUCTURE",
    "CSV_TABLE_LINE_MISSING": "STRUCTURE",
    "CSV_HEADER_LINE_MISSING": "STRUCTURE",
    "CSV_TABLE_NOT_IN_LOAD_SEQUENCE": "SEQUENCE",
    "CSV_TABLE_NOT_IN_DATA_DICTIONARY": "DATA_DICTIONARY",
    "CSV_UNKNOWN_COLUMN": "DATA_DICTIONARY",
    "CSV_DATE_ALTER_SESSION_MISSING": "DATE_FORMAT",
    "CSV_ROW_COUNT_MISMATCH": "SEQUENCE",
}

TITLE_BY_CODE = {
    "ZIP_MANIFEST_MISSING": "ZIP manifest missing",
    "ZIP_CSV_MISSING": "ZIP CSV files missing",
    "CSV_TABLE_LINE_MISSING": "CSV table line missing",
    "CSV_HEADER_LINE_MISSING": "CSV header line missing",
    "CSV_TABLE_NOT_IN_LOAD_SEQUENCE": "CSV table outside load sequence",
    "CSV_TABLE_NOT_IN_DATA_DICTIONARY": "Unknown OTM Data Dictionary table",
    "CSV_UNKNOWN_COLUMN": "Unknown OTM Data Dictionary column",
    "CSV_DATE_ALTER_SESSION_MISSING": "Missing OTM date format directive",
    "CSV_ROW_COUNT_MISMATCH": "CSV row count differs from package sequence",
}

DESCRIPTION_BY_CODE = {
    "ZIP_MANIFEST_MISSING": "The package ZIP does not include manifest.json and needs review before load planning continues.",
    "ZIP_CSV_MISSING": "The package ZIP does not include CSV files under csv/ and needs review before load planning continues.",
    "CSV_TABLE_LINE_MISSING": "A CSV file is missing the expected table-name line and needs review before load planning continues.",
    "CSV_HEADER_LINE_MISSING": "A CSV file is missing the expected column-header line and needs review before load planning continues.",
    "CSV_TABLE_NOT_IN_LOAD_SEQUENCE": "A CSV table was not found in the package load sequence and needs review before load planning continues.",
    "CSV_TABLE_NOT_IN_DATA_DICTIONARY": "A CSV table was not found in the local OTM Data Dictionary and needs review before load planning continues.",
    "CSV_UNKNOWN_COLUMN": "A CSV column was not found in the local OTM Data Dictionary and needs review before load planning continues.",
    "CSV_DATE_ALTER_SESSION_MISSING": "A CSV includes DATE columns but does not declare the expected NLS date format before value lines.",
    "CSV_ROW_COUNT_MISMATCH": "A CSV row count differs from the package load sequence and needs review before load planning continues.",
}


def serialize_review_item(item: LoadPlanReviewItem) -> dict[str, object]:
    return {
        "id": item.id,
        "project_id": item.project_id,
        "environment_id": item.environment_id,
        "profile_id": item.profile_id,
        "package_id": item.package_id,
        "zip_analysis_id": item.zip_analysis_id,
        "source_type": item.source_type,
        "source_code": item.source_code,
        "severity": item.severity,
        "status": item.status,
        "category": item.category,
        "table_name": item.table_name,
        "file_name": item.file_name,
        "title": item.title,
        "description": item.description,
        "details": parse_json_object(item.details_json),
        "created_by": item.created_by,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


def latest_review_decision(db: Session, item_id: str) -> LoadPlanReviewDecision | None:
    return (
        db.query(LoadPlanReviewDecision)
        .filter(LoadPlanReviewDecision.review_item_id == item_id)
        .order_by(LoadPlanReviewDecision.decided_at.desc(), LoadPlanReviewDecision.created_at.desc())
        .first()
    )


def serialize_review_item_with_latest_decision(db: Session, item: LoadPlanReviewItem) -> dict[str, object]:
    payload = serialize_review_item(item)
    decision = latest_review_decision(db, item.id)
    payload.update(
        {
            "latest_decision_id": decision.id if decision is not None else None,
            "latest_decision_status": decision.decision_status if decision is not None else None,
            "latest_decided_at": decision.decided_at.isoformat() if decision is not None and decision.decided_at else None,
        }
    )
    return payload


def serialize_review_decision(db: Session, decision: LoadPlanReviewDecision) -> dict[str, object]:
    item = db.query(LoadPlanReviewItem).filter(LoadPlanReviewItem.id == decision.review_item_id).one()
    catalog_context = catalog_context_for_package_id(db, decision.package_id)
    return {
        "id": decision.id,
        "project_id": decision.project_id,
        "environment_id": decision.environment_id,
        "profile_id": decision.profile_id,
        "package_id": decision.package_id,
        "review_item_id": decision.review_item_id,
        "decision_status": decision.decision_status,
        "decision_note": decision.decision_note,
        "evidence_id": decision.evidence_id,
        "decided_by": decision.decided_by,
        "decided_at": decision.decided_at.isoformat() if decision.decided_at else None,
        **catalog_context,
        "review_item": serialize_review_item_with_latest_decision(db, item),
    }


def catalog_context_for_package_id(db: Session, package_id: str) -> dict[str, object]:
    package = db.query(LoadPlanPackage).filter(LoadPlanPackage.id == package_id).first()
    if package is None:
        return {}
    summary = parse_json_object(package.summary_json)
    return {
        key: summary[key]
        for key in ("catalog_macro_object_code", "catalog_load_plan_path")
        if summary.get(key)
    }


def decide_review_item(
    db: Session,
    *,
    item: LoadPlanReviewItem,
    decision_status: str,
    decision_note: str,
    decided_by: str,
) -> LoadPlanReviewDecision:
    normalized_status = decision_status.strip()
    if normalized_status not in ALLOWED_DECISION_STATUSES:
        allowed = ", ".join(sorted(ALLOWED_DECISION_STATUSES))
        raise ValueError(f"Decision status must be one of: {allowed}.")

    decided_at = utcnow()
    catalog_context = catalog_context_for_package_id(db, item.package_id)
    evidence = Evidence(
        project_id=item.project_id,
        source_module="load_plan",
        evidence_type="load_plan_review_decision",
        status="CREATED",
        summary_json=json.dumps(
            {
                "source_entity_type": item.source_type,
                "source_entity_id": item.id,
                "review_item_id": item.id,
                "package_id": item.package_id,
                "decision_status": normalized_status,
                "decision_note_present": bool(decision_note.strip()),
                "decided_by": decided_by,
                "decided_at": decided_at.isoformat(),
                **catalog_context,
            },
            sort_keys=True,
        ),
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db.add(evidence)
    db.flush()

    decision = LoadPlanReviewDecision(
        project_id=item.project_id,
        environment_id=item.environment_id,
        profile_id=item.profile_id,
        package_id=item.package_id,
        review_item_id=item.id,
        decision_status=normalized_status,
        decision_note=decision_note,
        evidence_id=evidence.id,
        decided_by=decided_by,
        decided_at=decided_at,
    )
    item.status = normalized_status
    item.updated_at = decided_at
    db.add(decision)
    db.add(
        AuditLog(
            actor_user_id=decided_by,
            action="load_plan.review_queue.decide",
            target_type="load_plan_review_item",
            target_id=item.id,
            metadata_json=json.dumps(
                {
                    "package_id": item.package_id,
                    "decision_status": normalized_status,
                    "evidence_id": evidence.id,
                    "decision_note_present": bool(decision_note.strip()),
                },
                sort_keys=True,
            ),
        )
    )
    db.add(
        DomainEvent(
            event_type="load_plan.review_queue.decided",
            source_module="load_plan",
            project_id=item.project_id,
            aggregate_type="load_plan_review_item",
            aggregate_id=item.id,
            payload_json=json.dumps(
                {
                    "package_id": item.package_id,
                    "decision_status": normalized_status,
                    "evidence_id": evidence.id,
                    "decision_note_present": bool(decision_note.strip()),
                },
                sort_keys=True,
            ),
            status="PENDING",
        )
    )
    db.commit()
    db.refresh(decision)
    db.refresh(item)
    return decision


def review_item_identity(finding: dict[str, object]) -> tuple[str, str | None, str | None]:
    return (
        str(finding.get("code", "UNKNOWN_FINDING")),
        str(finding["table_name"]) if finding.get("table_name") is not None else None,
        str(finding["file_name"]) if finding.get("file_name") is not None else None,
    )


def existing_review_item(
    db: Session,
    *,
    analysis_id: str,
    source_code: str,
    table_name: str | None,
    file_name: str | None,
) -> LoadPlanReviewItem | None:
    query = (
        db.query(LoadPlanReviewItem)
        .filter(LoadPlanReviewItem.zip_analysis_id == analysis_id)
        .filter(LoadPlanReviewItem.source_type == SOURCE_TYPE)
        .filter(LoadPlanReviewItem.source_code == source_code)
    )
    query = query.filter(
        LoadPlanReviewItem.table_name.is_(None) if table_name is None else LoadPlanReviewItem.table_name == table_name
    )
    query = query.filter(
        LoadPlanReviewItem.file_name.is_(None) if file_name is None else LoadPlanReviewItem.file_name == file_name
    )
    return query.first()


def build_review_item(
    *,
    analysis: LoadPlanZipAnalysis,
    finding: dict[str, object],
    created_by: str,
) -> LoadPlanReviewItem:
    source_code, table_name, file_name = review_item_identity(finding)
    category = CATEGORY_BY_CODE.get(source_code, "PACKAGE")
    title = TITLE_BY_CODE.get(source_code, "Package finding requires review")
    description = DESCRIPTION_BY_CODE.get(
        source_code,
        "A local package analysis finding needs review before load planning continues.",
    )
    severity = str(finding.get("severity", "WARNING"))
    details = finding.get("details", {})
    details_json = json.dumps(details if isinstance(details, dict) else {}, sort_keys=True)
    return LoadPlanReviewItem(
        project_id=analysis.project_id,
        environment_id=analysis.environment_id,
        profile_id=analysis.profile_id,
        package_id=analysis.package_id,
        zip_analysis_id=analysis.id,
        source_type=SOURCE_TYPE,
        source_code=source_code,
        severity=severity,
        status=PENDING_STATUS,
        category=category,
        table_name=table_name,
        file_name=file_name,
        title=title,
        description=description,
        details_json=details_json,
        created_by=created_by,
    )


def generate_review_queue_from_zip_analysis(
    db: Session,
    *,
    analysis: LoadPlanZipAnalysis,
    generated_by: str,
) -> dict[str, object]:
    if analysis.status != "ANALYZED":
        raise ValueError("ZIP Analysis must be ANALYZED before review queue generation.")
    findings = parse_json_list(analysis.findings_json)
    selected = [item for item in findings if item.get("severity") in {"ERROR", "WARNING"}]
    created: list[LoadPlanReviewItem] = []
    existing: list[LoadPlanReviewItem] = []

    for finding in selected:
        source_code, table_name, file_name = review_item_identity(finding)
        current = existing_review_item(
            db,
            analysis_id=analysis.id,
            source_code=source_code,
            table_name=table_name,
            file_name=file_name,
        )
        if current is not None:
            existing.append(current)
            continue
        item = build_review_item(analysis=analysis, finding=finding, created_by=generated_by)
        db.add(item)
        db.flush()
        created.append(item)

    db.add(
        AuditLog(
            actor_user_id=generated_by,
            action="load_plan.review_queue.generate_from_zip_analysis",
            target_type="load_plan_zip_analysis",
            target_id=analysis.id,
            metadata_json=json.dumps(
                {
                    "package_id": analysis.package_id,
                    "created_count": len(created),
                    "existing_count": len(existing),
                    "selected_finding_count": len(selected),
                },
                sort_keys=True,
            ),
        )
    )
    db.add(
        DomainEvent(
            event_type="load_plan.review_queue.generated",
            source_module="load_plan",
            project_id=analysis.project_id,
            aggregate_type="load_plan_zip_analysis",
            aggregate_id=analysis.id,
            payload_json=json.dumps(
                {
                    "package_id": analysis.package_id,
                    "created_count": len(created),
                    "existing_count": len(existing),
                },
                sort_keys=True,
            ),
            status="PENDING",
        )
    )
    db.commit()
    for item in created + existing:
        db.refresh(item)
    return {
        "analysis_id": analysis.id,
        "package_id": analysis.package_id,
        "created_count": len(created),
        "existing_count": len(existing),
        "items": [serialize_review_item(item) for item in created + existing],
    }
