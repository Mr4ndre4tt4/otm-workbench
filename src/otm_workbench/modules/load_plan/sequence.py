import json
from pathlib import Path

from sqlalchemy.orm import Session

from otm_workbench.models import (
    AuditLog,
    DomainEvent,
    Evidence,
    LoadPlanPackage,
    LoadPlanReviewDecision,
    LoadPlanReviewItem,
    LoadPlanSequenceSnapshot,
    LoadPlanZipAnalysis,
    utcnow,
)
from otm_workbench.modules.load_plan.packages import parse_json_list, parse_json_object


READY_STATUS = "READY_FOR_REVIEW"
BLOCKED_STATUS = "BLOCKED"


def blocker(
    code: str,
    severity: str,
    message: str,
    *,
    table_name: str | None = None,
    source_type: str | None = None,
    source_id: str | None = None,
    details: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "code": code,
        "severity": severity,
        "table_name": table_name,
        "source_type": source_type,
        "source_id": source_id,
        "message": message,
        "details": details or {},
    }


def serialize_sequence_snapshot(snapshot: LoadPlanSequenceSnapshot) -> dict[str, object]:
    return {
        "id": snapshot.id,
        "project_id": snapshot.project_id,
        "environment_id": snapshot.environment_id,
        "profile_id": snapshot.profile_id,
        "package_id": snapshot.package_id,
        "status": snapshot.status,
        "sequence": parse_json_list(snapshot.sequence_json),
        "blockers": parse_json_list(snapshot.blockers_json),
        "summary": parse_json_object(snapshot.summary_json),
        "evidence_id": snapshot.evidence_id,
        "generated_by": snapshot.generated_by,
        "generated_at": snapshot.generated_at.isoformat() if snapshot.generated_at else None,
    }


def latest_zip_analysis(db: Session, package_id: str) -> LoadPlanZipAnalysis | None:
    return (
        db.query(LoadPlanZipAnalysis)
        .filter(LoadPlanZipAnalysis.package_id == package_id)
        .order_by(LoadPlanZipAnalysis.analyzed_at.desc(), LoadPlanZipAnalysis.created_at.desc())
        .first()
    )


def latest_sequence_snapshot(db: Session, package_id: str) -> LoadPlanSequenceSnapshot | None:
    return (
        db.query(LoadPlanSequenceSnapshot)
        .filter(LoadPlanSequenceSnapshot.package_id == package_id)
        .order_by(LoadPlanSequenceSnapshot.generated_at.desc(), LoadPlanSequenceSnapshot.created_at.desc())
        .first()
    )


def load_dictionary_parent_tables(dictionary_root: Path, table_name: str) -> tuple[bool, list[str]]:
    normalized = table_name.upper()
    for path in (dictionary_root / f"{normalized}.json", dictionary_root / f"{normalized.lower()}.json"):
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
            parents = sorted(
                {
                    str(foreign_key.get("parentTableName", "")).upper()
                    for foreign_key in payload.get("foreignKeys", [])
                    if foreign_key.get("parentTableName")
                }
            )
            return True, parents
    return False, []


def latest_decision_for_item(db: Session, item_id: str) -> LoadPlanReviewDecision | None:
    return (
        db.query(LoadPlanReviewDecision)
        .filter(LoadPlanReviewDecision.review_item_id == item_id)
        .order_by(LoadPlanReviewDecision.decided_at.desc(), LoadPlanReviewDecision.created_at.desc())
        .first()
    )


def review_summary_for_table(db: Session, package_id: str, table_name: str) -> tuple[dict[str, int], list[dict[str, object]]]:
    summary = {
        "pending_count": 0,
        "needs_manual_action_count": 0,
        "rejected_count": 0,
        "excluded_from_cutover_count": 0,
        "confirmed_count": 0,
    }
    blockers: list[dict[str, object]] = []
    items = (
        db.query(LoadPlanReviewItem)
        .filter(LoadPlanReviewItem.package_id == package_id)
        .filter(LoadPlanReviewItem.table_name == table_name)
        .order_by(LoadPlanReviewItem.created_at)
        .all()
    )
    for item in items:
        decision = latest_decision_for_item(db, item.id)
        if decision is None or item.status == "PENDING_REVIEW":
            summary["pending_count"] += 1
            blockers.append(
                blocker(
                    "REVIEW_ITEM_PENDING",
                    "ERROR",
                    "A review item still needs a decision before later readiness checks.",
                    table_name=table_name,
                    source_type="load_plan_review_item",
                    source_id=item.id,
                )
            )
            continue
        if decision.decision_status == "CONFIRMED":
            summary["confirmed_count"] += 1
        elif decision.decision_status == "REJECTED":
            summary["rejected_count"] += 1
            blockers.append(
                blocker(
                    "REVIEW_ITEM_REJECTED",
                    "ERROR",
                    "A review item was rejected.",
                    table_name=table_name,
                    source_type="load_plan_review_decision",
                    source_id=decision.id,
                )
            )
        elif decision.decision_status == "NEEDS_MANUAL_ACTION":
            summary["needs_manual_action_count"] += 1
            blockers.append(
                blocker(
                    "REVIEW_ITEM_NEEDS_MANUAL_ACTION",
                    "ERROR",
                    "A review item requires manual action.",
                    table_name=table_name,
                    source_type="load_plan_review_decision",
                    source_id=decision.id,
                )
            )
        elif decision.decision_status == "EXCLUDED_FROM_CUTOVER":
            summary["excluded_from_cutover_count"] += 1
            blockers.append(
                blocker(
                    "REVIEW_ITEM_EXCLUDED_FROM_CUTOVER",
                    "WARNING",
                    "A review item was excluded from later cutover planning.",
                    table_name=table_name,
                    source_type="load_plan_review_decision",
                    source_id=decision.id,
                )
            )
    return summary, blockers


def derive_next_actions(blockers: list[dict[str, object]]) -> list[str]:
    codes = {str(item["code"]) for item in blockers}
    actions: list[str] = []
    if "ZIP_ANALYSIS_MISSING" in codes:
        actions.append("run_zip_analysis")
    if "REVIEW_ITEM_PENDING" in codes:
        actions.append("decide_review_items")
    if "REVIEW_ITEM_NEEDS_MANUAL_ACTION" in codes:
        actions.append("resolve_manual_actions")
    if "REVIEW_ITEM_REJECTED" in codes:
        actions.append("remove_rejected_items_or_rework_package")
    if "REVIEW_ITEM_EXCLUDED_FROM_CUTOVER" in codes:
        actions.append("review_exclusions")
    if "PACKAGE_PARENT_TABLE_MISSING" in codes or "DICTIONARY_TABLE_MISSING" in codes:
        actions.append("review_package_dependencies")
    if not actions:
        actions.append("ready_for_later_readiness")
    return actions


def catalog_context_for_package(package: LoadPlanPackage) -> dict[str, object]:
    summary = parse_json_object(package.summary_json)
    return {
        key: summary[key]
        for key in ("catalog_macro_object_code", "catalog_load_plan_path")
        if summary.get(key)
    }


def generate_sequence_snapshot(
    db: Session,
    *,
    package: LoadPlanPackage,
    dictionary_root: Path,
    generated_by: str,
) -> LoadPlanSequenceSnapshot:
    if package.status != "REGISTERED":
        raise ValueError("Load Plan package must be REGISTERED before sequence snapshot generation.")
    if not package.artifact_id or not package.manifest_id:
        raise ValueError("Load Plan package must reference source artifact and manifest before sequence snapshot generation.")
    load_sequence = parse_json_list(package.load_sequence_json)
    if not load_sequence:
        raise ValueError("Load Plan package must have a load sequence before sequence snapshot generation.")

    catalog_context = catalog_context_for_package(package)
    latest_analysis = latest_zip_analysis(db, package.id)
    package_tables = {str(item["table_name"]).upper() for item in load_sequence if item.get("table_name")}
    blockers: list[dict[str, object]] = []
    sequence_rows: list[dict[str, object]] = []
    findings = parse_json_list(latest_analysis.findings_json) if latest_analysis else []
    if latest_analysis is None:
        blockers.append(
            blocker(
                "ZIP_ANALYSIS_MISSING",
                "ERROR",
                "No ZIP Analysis exists for this package.",
                source_type="load_plan_package",
                source_id=package.id,
            )
        )
    elif any(item.get("severity") == "ERROR" for item in findings):
        blockers.append(
            blocker(
                "ZIP_ANALYSIS_HAS_ERRORS",
                "ERROR",
                "Latest ZIP Analysis has error findings.",
                source_type="load_plan_zip_analysis",
                source_id=latest_analysis.id,
            )
        )

    for item in load_sequence:
        table_name = str(item["table_name"]).upper()
        dictionary_found, parent_tables = load_dictionary_parent_tables(dictionary_root, table_name)
        missing_parent_tables = [parent for parent in parent_tables if parent not in package_tables]
        if not dictionary_found:
            blockers.append(
                blocker(
                    "DICTIONARY_TABLE_MISSING",
                    "ERROR",
                    "Table JSON is missing from the local OTM Data Dictionary.",
                    table_name=table_name,
                    source_type="load_plan_package",
                    source_id=package.id,
                )
            )
        for parent in missing_parent_tables:
            blockers.append(
                blocker(
                    "PACKAGE_PARENT_TABLE_MISSING",
                    "ERROR",
                    "A Data Dictionary parent table is not present in this package sequence.",
                    table_name=table_name,
                    source_type="otm_data_dictionary",
                    source_id=parent,
                    details={"parent_table_name": parent},
                )
            )
        review_summary, review_blockers = review_summary_for_table(db, package.id, table_name)
        blockers.extend(review_blockers)
        table_findings = [finding for finding in findings if str(finding.get("table_name", "")).upper() == table_name]
        sequence_rows.append(
            {
                "position": int(item.get("position", 0)),
                "table_name": table_name,
                "row_count": int(item.get("row_count", 0)),
                "requirement_level": str(item.get("requirement_level", "OPTIONAL")),
                "dictionary_table_found": dictionary_found,
                "parent_tables": parent_tables,
                "missing_parent_tables_in_package": missing_parent_tables,
                "zip_analysis": {
                    "latest_analysis_id": latest_analysis.id if latest_analysis else None,
                    "finding_count": len(table_findings),
                    "error_count": sum(1 for finding in table_findings if finding.get("severity") == "ERROR"),
                    "warning_count": sum(1 for finding in table_findings if finding.get("severity") == "WARNING"),
                },
                "review": review_summary,
            }
        )

    error_count = sum(1 for item in blockers if item["severity"] == "ERROR")
    warning_count = sum(1 for item in blockers if item["severity"] == "WARNING")
    status = BLOCKED_STATUS if blockers else READY_STATUS
    summary = {
        "table_count": len(sequence_rows),
        "row_count": sum(int(item.get("row_count", 0)) for item in sequence_rows),
        "blocker_count": len(blockers),
        "error_count": error_count,
        "warning_count": warning_count,
        "next_actions": derive_next_actions(blockers),
        **catalog_context,
    }
    generated_at = utcnow()
    snapshot = LoadPlanSequenceSnapshot(
        project_id=package.project_id,
        environment_id=package.environment_id,
        profile_id=package.profile_id,
        package_id=package.id,
        status=status,
        sequence_json=json.dumps(sequence_rows, sort_keys=True),
        blockers_json=json.dumps(blockers, sort_keys=True),
        summary_json=json.dumps(summary, sort_keys=True),
        generated_by=generated_by,
        generated_at=generated_at,
    )
    db.add(snapshot)
    db.flush()

    evidence_summary = {
        "source_entity_type": "load_plan_sequence_snapshot",
        "source_entity_id": snapshot.id,
        "package_id": package.id,
        "status": status,
        "table_count": summary["table_count"],
        "row_count": summary["row_count"],
        "blocker_count": summary["blocker_count"],
        "error_count": summary["error_count"],
        "warning_count": summary["warning_count"],
        **catalog_context,
    }
    evidence = Evidence(
        project_id=package.project_id,
        profile_id=package.profile_id,
        environment_id=package.environment_id,
        domain_name=package.domain_name,
        visibility="PROJECT",
        source_module="load_plan",
        evidence_type="load_plan_sequence_snapshot",
        summary_json=json.dumps(evidence_summary, sort_keys=True),
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db.add(evidence)
    db.flush()
    snapshot.evidence_id = evidence.id
    db.add(
        AuditLog(
            actor_user_id=generated_by,
            action="load_plan.sequence.snapshot.generate",
            target_type="load_plan_sequence_snapshot",
            target_id=snapshot.id,
            metadata_json=json.dumps(
                {
                    "package_id": package.id,
                    "status": status,
                    "evidence_id": evidence.id,
                    "blocker_count": summary["blocker_count"],
                    **catalog_context,
                },
                sort_keys=True,
            ),
        )
    )
    db.add(
        DomainEvent(
            event_type="load_plan.sequence.snapshot.generated",
            source_module="load_plan",
            project_id=package.project_id,
            aggregate_type="load_plan_sequence_snapshot",
            aggregate_id=snapshot.id,
            payload_json=json.dumps({"package_id": package.id, "status": status, **catalog_context}, sort_keys=True),
            status="PENDING",
        )
    )
    db.commit()
    db.refresh(snapshot)
    return snapshot
