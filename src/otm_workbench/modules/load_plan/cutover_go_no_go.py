import json

from sqlalchemy.orm import Session

from otm_workbench.models import AuditLog, CutoverChecklist, DomainEvent, Evidence, LoadPlanPackage
from otm_workbench.modules.load_plan.cutover_checklist import checklist_readiness_payload
from otm_workbench.modules.load_plan.cutover_package import (
    catalog_context_for_checklist,
    latest_checklist_readiness_evidence,
)
from otm_workbench.modules.load_plan.packages import parse_json_object
from otm_workbench.modules.rates.exports import iso_now


GO_DECISION = "GO"
NO_GO_DECISION = "NO_GO"


def decision_blocker(code: str, message: str) -> dict[str, object]:
    return {"code": code, "severity": "ERROR", "message": message}


def latest_cutover_package_evidence(db: Session, checklist_id: str) -> Evidence | None:
    candidates = (
        db.query(Evidence)
        .filter(Evidence.source_module == "load_plan")
        .filter(Evidence.evidence_type == "cutover_package_export")
        .filter(Evidence.client_safe.is_(True))
        .order_by(Evidence.created_at.desc())
        .all()
    )
    for evidence in candidates:
        summary = parse_json_object(evidence.summary_json)
        if summary.get("checklist_id") == checklist_id:
            return evidence
    return None


def decide_cutover_go_no_go(
    db: Session,
    *,
    checklist: CutoverChecklist,
    package: LoadPlanPackage,
    decided_by: str,
) -> dict[str, object]:
    readiness_evidence = latest_checklist_readiness_evidence(db, checklist.id)
    cutover_package_evidence = latest_cutover_package_evidence(db, checklist.id)
    blockers: list[dict[str, object]] = []
    readiness_status = None
    live_readiness = checklist_readiness_payload(db, checklist)
    live_readiness_status = live_readiness["status"]
    live_readiness_blockers = list(live_readiness["blockers"])

    if readiness_evidence is None:
        blockers.append(
            decision_blocker("CUTOVER_CHECKLIST_READINESS_MISSING", "Generate Cutover Checklist readiness first.")
        )
    else:
        readiness_summary = parse_json_object(readiness_evidence.summary_json)
        readiness_status = live_readiness_status or readiness_summary.get("status")
        if live_readiness_status != "READY":
            blockers.extend(live_readiness_blockers)
            if not live_readiness_blockers:
                blockers.append(
                    decision_blocker("CUTOVER_CHECKLIST_NOT_READY", "Current Cutover Checklist readiness is not READY.")
                )

    if cutover_package_evidence is None:
        blockers.append(decision_blocker("CUTOVER_PACKAGE_EXPORT_MISSING", "Export the Cutover package first."))

    decision = GO_DECISION if not blockers else NO_GO_DECISION
    catalog_context = catalog_context_for_checklist(checklist)
    summary = {
        "decision": decision,
        "checklist_id": checklist.id,
        "package_id": package.id,
        "readiness_status": readiness_status,
        "readiness_evidence_id": readiness_evidence.id if readiness_evidence else None,
        "cutover_package_evidence_id": cutover_package_evidence.id if cutover_package_evidence else None,
        "live_readiness_summary": live_readiness["summary"],
        "blocker_count": len(blockers),
        "decided_at": iso_now(),
        "decided_by": decided_by,
        **catalog_context,
    }
    evidence = Evidence(
        project_id=checklist.project_id,
        source_module="load_plan",
        evidence_type="cutover_go_no_go_decision",
        summary_json=json.dumps(summary, sort_keys=True),
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db.add(evidence)
    db.flush()

    payload = {**summary, "evidence_id": evidence.id, "blockers": blockers}
    audit_payload = dict(payload)
    audit_payload.pop("decided_by", None)
    db.add(
        AuditLog(
            actor_user_id=decided_by,
            action="load_plan.cutover_go_no_go.decide",
            target_type="cutover_checklist",
            target_id=checklist.id,
            metadata_json=json.dumps(audit_payload, sort_keys=True),
        )
    )
    db.add(
        DomainEvent(
            event_type="load_plan.cutover_go_no_go.decided",
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
