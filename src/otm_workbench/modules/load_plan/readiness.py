import json

from sqlalchemy.orm import Session

from otm_workbench.models import (
    AuditLog,
    DomainEvent,
    Evidence,
    LoadPlanCutoverReadiness,
    LoadPlanPackage,
    LoadPlanSequenceSnapshot,
    utcnow,
)
from otm_workbench.modules.load_plan.packages import parse_json_list, parse_json_object
from otm_workbench.modules.load_plan.sequence import latest_sequence_snapshot


READY_STATUS = "READY"
BLOCKED_STATUS = "BLOCKED"
NEEDS_REVIEW_STATUS = "NEEDS_REVIEW"
MISSING_SEQUENCE_STATUS = "MISSING_SEQUENCE"


def readiness_blocker(
    code: str,
    severity: str,
    message: str,
    *,
    source_type: str | None = None,
    source_id: str | None = None,
) -> dict[str, object]:
    return {
        "code": code,
        "severity": severity,
        "table_name": None,
        "source_type": source_type,
        "source_id": source_id,
        "message": message,
        "details": {},
    }


def readiness_status_from_blockers(
    blockers: list[dict[str, object]],
    sequence_snapshot: LoadPlanSequenceSnapshot | None,
) -> str:
    if sequence_snapshot is None:
        return MISSING_SEQUENCE_STATUS
    if any(item.get("severity") == "ERROR" for item in blockers):
        return BLOCKED_STATUS
    if blockers:
        return NEEDS_REVIEW_STATUS
    return READY_STATUS


def readiness_checks(
    status: str,
    sequence_snapshot: LoadPlanSequenceSnapshot | None,
    blockers: list[dict[str, object]],
) -> list[dict[str, object]]:
    return [
        {
            "code": "SEQUENCE_SNAPSHOT_AVAILABLE",
            "status": "PASSED" if sequence_snapshot is not None else "FAILED",
            "message": "Latest sequence snapshot is available."
            if sequence_snapshot is not None
            else "Generate a sequence snapshot first.",
        },
        {
            "code": "NO_ERROR_BLOCKERS",
            "status": "PASSED" if not any(item.get("severity") == "ERROR" for item in blockers) else "FAILED",
            "message": "No error blockers were found."
            if status != BLOCKED_STATUS
            else "Latest sequence snapshot contains error blockers.",
        },
        {
            "code": "NO_WARNING_BLOCKERS",
            "status": "PASSED" if not any(item.get("severity") == "WARNING" for item in blockers) else "REVIEW",
            "message": "No warning blockers were found."
            if status != NEEDS_REVIEW_STATUS
            else "Latest sequence snapshot contains warning blockers.",
        },
    ]


def next_actions_for_status(status: str) -> list[str]:
    if status == MISSING_SEQUENCE_STATUS:
        return ["generate_sequence_snapshot"]
    if status == BLOCKED_STATUS:
        return ["resolve_sequence_blockers"]
    if status == NEEDS_REVIEW_STATUS:
        return ["review_warnings"]
    return ["ready_for_cutover_export"]


def catalog_context_for_package(package: LoadPlanPackage) -> dict[str, object]:
    summary = parse_json_object(package.summary_json)
    return {
        key: summary[key]
        for key in ("catalog_macro_object_code", "catalog_load_plan_path")
        if summary.get(key)
    }


def serialize_cutover_readiness(readiness: LoadPlanCutoverReadiness) -> dict[str, object]:
    return {
        "id": readiness.id,
        "project_id": readiness.project_id,
        "environment_id": readiness.environment_id,
        "profile_id": readiness.profile_id,
        "package_id": readiness.package_id,
        "sequence_snapshot_id": readiness.sequence_snapshot_id,
        "status": readiness.status,
        "readiness": parse_json_object(readiness.readiness_json),
        "blockers": parse_json_list(readiness.blockers_json),
        "summary": parse_json_object(readiness.summary_json),
        "evidence_id": readiness.evidence_id,
        "generated_by": readiness.generated_by,
        "generated_at": readiness.generated_at.isoformat() if readiness.generated_at else None,
    }


def latest_cutover_readiness(db: Session, package_id: str) -> LoadPlanCutoverReadiness | None:
    return (
        db.query(LoadPlanCutoverReadiness)
        .filter(LoadPlanCutoverReadiness.package_id == package_id)
        .order_by(LoadPlanCutoverReadiness.generated_at.desc(), LoadPlanCutoverReadiness.created_at.desc())
        .first()
    )


def summarize_readiness_stub(status: str, blockers: list[dict[str, object]]) -> dict[str, object]:
    error_count = sum(1 for item in blockers if item.get("severity") == "ERROR")
    warning_count = sum(1 for item in blockers if item.get("severity") == "WARNING")
    return {
        "package_count": 1,
        "ready_count": 1 if status == READY_STATUS else 0,
        "blocked_count": 1 if status == BLOCKED_STATUS else 0,
        "needs_review_count": 1 if status == NEEDS_REVIEW_STATUS else 0,
        "missing_sequence_count": 1 if status == MISSING_SEQUENCE_STATUS else 0,
        "blocker_count": len(blockers),
        "error_count": error_count,
        "warning_count": warning_count,
        "next_actions": next_actions_for_status(status),
    }


def summarize_readiness(items: list[LoadPlanCutoverReadiness]) -> dict[str, object]:
    blockers = [blocker for item in items for blocker in parse_json_list(item.blockers_json)]
    statuses = [item.status for item in items]
    error_count = sum(1 for item in blockers if item.get("severity") == "ERROR")
    warning_count = sum(1 for item in blockers if item.get("severity") == "WARNING")
    next_actions: list[str] = []
    for status in [MISSING_SEQUENCE_STATUS, BLOCKED_STATUS, NEEDS_REVIEW_STATUS, READY_STATUS]:
        if status in statuses:
            for action in next_actions_for_status(status):
                if action not in next_actions:
                    next_actions.append(action)
    return {
        "package_count": len(items),
        "ready_count": statuses.count(READY_STATUS),
        "blocked_count": statuses.count(BLOCKED_STATUS),
        "needs_review_count": statuses.count(NEEDS_REVIEW_STATUS),
        "missing_sequence_count": statuses.count(MISSING_SEQUENCE_STATUS),
        "blocker_count": len(blockers),
        "error_count": error_count,
        "warning_count": warning_count,
        "next_actions": next_actions,
    }


def generate_readiness_for_package(
    db: Session,
    *,
    package: LoadPlanPackage,
    generated_by: str,
) -> LoadPlanCutoverReadiness:
    sequence_snapshot = latest_sequence_snapshot(db, package.id)
    blockers = (
        [
            readiness_blocker(
                "SEQUENCE_SNAPSHOT_MISSING",
                "ERROR",
                "No sequence snapshot exists for this package.",
                source_type="load_plan_package",
                source_id=package.id,
            )
        ]
        if sequence_snapshot is None
        else parse_json_list(sequence_snapshot.blockers_json)
    )
    status = readiness_status_from_blockers(blockers, sequence_snapshot)
    catalog_context = catalog_context_for_package(package)
    readiness_payload = {
        "package_id": package.id,
        "sequence_snapshot_id": sequence_snapshot.id if sequence_snapshot is not None else None,
        "status": status,
        "checks": readiness_checks(status, sequence_snapshot, blockers),
    }
    summary = summarize_readiness_stub(status, blockers)
    summary.update(catalog_context)
    generated_at = utcnow()
    readiness = LoadPlanCutoverReadiness(
        project_id=package.project_id,
        environment_id=package.environment_id,
        profile_id=package.profile_id,
        package_id=package.id,
        sequence_snapshot_id=sequence_snapshot.id if sequence_snapshot is not None else None,
        status=status,
        readiness_json=json.dumps(readiness_payload, sort_keys=True),
        blockers_json=json.dumps(blockers, sort_keys=True),
        summary_json=json.dumps(summary, sort_keys=True),
        generated_by=generated_by,
        generated_at=generated_at,
    )
    db.add(readiness)
    db.flush()

    evidence_summary = {
        "source_entity_type": "load_plan_cutover_readiness",
        "source_entity_id": readiness.id,
        "package_id": package.id,
        "sequence_snapshot_id": readiness.sequence_snapshot_id,
        "status": status,
        "blocker_count": summary["blocker_count"],
        "error_count": summary["error_count"],
        "warning_count": summary["warning_count"],
        **catalog_context,
    }
    evidence = Evidence(
        project_id=package.project_id,
        source_module="load_plan",
        evidence_type="load_plan_cutover_readiness",
        summary_json=json.dumps(evidence_summary, sort_keys=True),
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db.add(evidence)
    db.flush()
    readiness.evidence_id = evidence.id

    db.add(
        AuditLog(
            actor_user_id=generated_by,
            action="load_plan.cutover_readiness.generate",
            target_type="load_plan_cutover_readiness",
            target_id=readiness.id,
            metadata_json=json.dumps(
                {
                    "package_id": package.id,
                    "sequence_snapshot_id": readiness.sequence_snapshot_id,
                    "status": status,
                    "evidence_id": evidence.id,
                    "blocker_count": summary["blocker_count"],
                },
                sort_keys=True,
            ),
        )
    )
    db.add(
        DomainEvent(
            event_type="load_plan.cutover_readiness.generated",
            source_module="load_plan",
            project_id=package.project_id,
            aggregate_type="load_plan_cutover_readiness",
            aggregate_id=readiness.id,
            payload_json=json.dumps({"package_id": package.id, "status": status}, sort_keys=True),
            status="PENDING",
        )
    )
    db.flush()
    return readiness


def generate_cutover_readiness(
    db: Session,
    *,
    packages: list[LoadPlanPackage],
    generated_by: str,
) -> dict[str, object]:
    if not packages:
        raise ValueError("At least one registered Load Plan package is required for cutover readiness generation.")
    items = [generate_readiness_for_package(db, package=package, generated_by=generated_by) for package in packages]
    db.commit()
    for item in items:
        db.refresh(item)
    return {
        "items": [serialize_cutover_readiness(item) for item in items],
        "summary": summarize_readiness(items),
    }
