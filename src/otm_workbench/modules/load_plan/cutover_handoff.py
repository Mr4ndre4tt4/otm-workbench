import json

from sqlalchemy.orm import Session

from otm_workbench.models import (
    AuditLog,
    CutoverChecklist,
    DomainEvent,
    Evidence,
    LoadPlanCutoverHandoff,
    LoadPlanCutoverReadiness,
    LoadPlanPackage,
    LoadPlanReadinessExport,
    utcnow,
)
from otm_workbench.modules.load_plan.packages import parse_json_object


ELIGIBLE_STATUS = "ELIGIBLE"
INELIGIBLE_STATUS = "INELIGIBLE"
READY_READINESS_STATUS = "READY"
READY_FOR_CUTOVER_STATUS = "READY_FOR_CUTOVER"


def handoff_blocker(code: str, message: str) -> dict[str, object]:
    return {"code": code, "severity": "ERROR", "message": message, "details": {}}


def catalog_context_for_package(package: LoadPlanPackage) -> dict[str, object]:
    summary = parse_json_object(package.summary_json)
    return {
        key: summary[key]
        for key in ("catalog_macro_object_code", "catalog_load_plan_path")
        if summary.get(key)
    }


def serialize_cutover_handoff(handoff: LoadPlanCutoverHandoff) -> dict[str, object]:
    return {
        "id": handoff.id,
        "project_id": handoff.project_id,
        "environment_id": handoff.environment_id,
        "profile_id": handoff.profile_id,
        "package_id": handoff.package_id,
        "readiness_id": handoff.readiness_id,
        "readiness_export_id": handoff.readiness_export_id,
        "archive_evidence_id": handoff.archive_evidence_id,
        "status": handoff.status,
        "evidence_id": handoff.evidence_id,
        "summary": parse_json_object(handoff.summary_json),
        "committed_by": handoff.committed_by,
        "committed_at": handoff.committed_at.isoformat() if handoff.committed_at else None,
    }


def latest_ready_handoff(db: Session, package_id: str) -> LoadPlanCutoverHandoff | None:
    return (
        db.query(LoadPlanCutoverHandoff)
        .filter(LoadPlanCutoverHandoff.package_id == package_id)
        .filter(LoadPlanCutoverHandoff.status == READY_FOR_CUTOVER_STATUS)
        .order_by(LoadPlanCutoverHandoff.committed_at.desc(), LoadPlanCutoverHandoff.created_at.desc())
        .first()
    )


def latest_readiness(db: Session, package_id: str) -> LoadPlanCutoverReadiness | None:
    return (
        db.query(LoadPlanCutoverReadiness)
        .filter(LoadPlanCutoverReadiness.package_id == package_id)
        .order_by(LoadPlanCutoverReadiness.generated_at.desc(), LoadPlanCutoverReadiness.created_at.desc())
        .first()
    )


def latest_readiness_export(db: Session, readiness_id: str) -> LoadPlanReadinessExport | None:
    return (
        db.query(LoadPlanReadinessExport)
        .filter(LoadPlanReadinessExport.readiness_id == readiness_id)
        .order_by(LoadPlanReadinessExport.exported_at.desc(), LoadPlanReadinessExport.created_at.desc())
        .first()
    )


def archive_evidence_for_export(db: Session, export: LoadPlanReadinessExport) -> Evidence | None:
    if not export.evidence_id:
        return None
    return (
        db.query(Evidence)
        .filter(Evidence.source_module == "evidence_hub")
        .filter(Evidence.evidence_type == "evidence_hub_archive")
        .filter(Evidence.client_safe.is_(True))
        .filter(Evidence.summary_json.contains(export.evidence_id))
        .order_by(Evidence.created_at.desc())
        .first()
    )


def latest_cutover_checklist(db: Session, package_id: str) -> CutoverChecklist | None:
    return (
        db.query(CutoverChecklist)
        .filter(CutoverChecklist.package_id == package_id)
        .order_by(CutoverChecklist.created_at.desc())
        .first()
    )


def latest_checklist_readiness_evidence(db: Session, checklist_id: str) -> Evidence | None:
    return (
        db.query(Evidence)
        .filter(Evidence.source_module == "load_plan")
        .filter(Evidence.evidence_type == "cutover_checklist_readiness")
        .filter(Evidence.client_safe.is_(True))
        .filter(Evidence.summary_json.contains(checklist_id))
        .order_by(Evidence.created_at.desc())
        .first()
    )


def checklist_readiness_context(db: Session, package_id: str) -> dict[str, object]:
    checklist = latest_cutover_checklist(db, package_id)
    if checklist is None:
        return {
            "checklist_id": None,
            "checklist_readiness_status": None,
            "checklist_readiness_evidence_id": None,
            "blocker": None,
        }
    evidence = latest_checklist_readiness_evidence(db, checklist.id)
    if evidence is None:
        return {
            "checklist_id": checklist.id,
            "checklist_readiness_status": None,
            "checklist_readiness_evidence_id": None,
            "blocker": handoff_blocker(
                "CUTOVER_CHECKLIST_READINESS_MISSING",
                "Generate Cutover Checklist readiness first.",
            ),
        }
    summary = parse_json_object(evidence.summary_json)
    status = summary.get("status")
    if status != READY_READINESS_STATUS:
        return {
            "checklist_id": checklist.id,
            "checklist_readiness_status": status,
            "checklist_readiness_evidence_id": evidence.id,
            "blocker": handoff_blocker(
                "CUTOVER_CHECKLIST_NOT_READY",
                "Latest Cutover Checklist readiness is not READY.",
            ),
        }
    return {
        "checklist_id": checklist.id,
        "checklist_readiness_status": status,
        "checklist_readiness_evidence_id": evidence.id,
        "blocker": None,
    }


def cutover_handoff_eligibility(db: Session, package: LoadPlanPackage) -> dict[str, object]:
    readiness = latest_readiness(db, package.id)
    blockers: list[dict[str, object]] = []
    readiness_export = None
    archive_evidence = None
    catalog_context = catalog_context_for_package(package)
    checklist_context = checklist_readiness_context(db, package.id)

    if readiness is None:
        blockers.append(handoff_blocker("CUTOVER_READINESS_MISSING", "Generate cutover readiness first."))
    elif readiness.status != READY_READINESS_STATUS:
        blockers.append(handoff_blocker("CUTOVER_READINESS_NOT_READY", "Latest readiness is not READY."))
    else:
        readiness_export = latest_readiness_export(db, readiness.id)
        if readiness_export is None:
            blockers.append(handoff_blocker("READINESS_EXPORT_MISSING", "Export readiness first."))
        else:
            archive_evidence = archive_evidence_for_export(db, readiness_export)
            if archive_evidence is None:
                blockers.append(
                    handoff_blocker("EVIDENCE_ARCHIVE_MISSING", "Archive readiness export evidence first.")
                )
    if checklist_context["blocker"] is not None:
        blockers.append(checklist_context["blocker"])

    eligible = not blockers
    return {
        "package_id": package.id,
        "eligible": eligible,
        "status": ELIGIBLE_STATUS if eligible else INELIGIBLE_STATUS,
        "readiness_id": readiness.id if readiness else None,
        "readiness_status": readiness.status if readiness else None,
        "readiness_export_id": readiness_export.id if readiness_export else None,
        "readiness_export_evidence_id": readiness_export.evidence_id if readiness_export else None,
        "archive_evidence_id": archive_evidence.id if archive_evidence else None,
        "checklist_id": checklist_context["checklist_id"],
        "checklist_readiness_status": checklist_context["checklist_readiness_status"],
        "checklist_readiness_evidence_id": checklist_context["checklist_readiness_evidence_id"],
        "blockers": blockers,
        "next_actions": ["commit_cutover_handoff"] if eligible else [item["code"] for item in blockers],
        **catalog_context,
    }


def commit_cutover_handoff(
    db: Session,
    *,
    package: LoadPlanPackage,
    committed_by: str,
) -> LoadPlanCutoverHandoff:
    existing = latest_ready_handoff(db, package.id)
    if existing is not None:
        return existing

    eligibility = cutover_handoff_eligibility(db, package)
    if not eligibility["eligible"]:
        raise ValueError(json.dumps({"blockers": eligibility["blockers"]}, sort_keys=True))

    catalog_context = catalog_context_for_package(package)
    summary = {
        "package_id": package.id,
        "readiness_id": eligibility["readiness_id"],
        "readiness_status": eligibility["readiness_status"],
        "readiness_export_id": eligibility["readiness_export_id"],
        "archive_evidence_id": eligibility["archive_evidence_id"],
        "checklist_id": eligibility["checklist_id"],
        "checklist_readiness_status": eligibility["checklist_readiness_status"],
        "checklist_readiness_evidence_id": eligibility["checklist_readiness_evidence_id"],
        "status": READY_FOR_CUTOVER_STATUS,
        **catalog_context,
    }
    committed_at = utcnow()
    handoff = LoadPlanCutoverHandoff(
        project_id=package.project_id,
        environment_id=package.environment_id,
        profile_id=package.profile_id,
        package_id=package.id,
        readiness_id=str(eligibility["readiness_id"]),
        readiness_export_id=str(eligibility["readiness_export_id"]),
        archive_evidence_id=str(eligibility["archive_evidence_id"]),
        status=READY_FOR_CUTOVER_STATUS,
        summary_json=json.dumps(summary, sort_keys=True),
        committed_by=committed_by,
        committed_at=committed_at,
    )
    db.add(handoff)
    db.flush()

    evidence_summary = {
        "source_entity_type": "load_plan_cutover_handoff",
        "source_entity_id": handoff.id,
        **summary,
    }
    evidence = Evidence(
        project_id=package.project_id,
        source_module="load_plan",
        evidence_type="load_plan_cutover_handoff",
        summary_json=json.dumps(evidence_summary, sort_keys=True),
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db.add(evidence)
    db.flush()
    handoff.evidence_id = evidence.id

    db.add(
        AuditLog(
            actor_user_id=committed_by,
            action="load_plan.cutover_handoff.commit",
            target_type="load_plan_cutover_handoff",
            target_id=handoff.id,
            metadata_json=json.dumps(
                {
                    "package_id": package.id,
                    "readiness_id": handoff.readiness_id,
                    "readiness_export_id": handoff.readiness_export_id,
                    "archive_evidence_id": handoff.archive_evidence_id,
                    "checklist_id": eligibility["checklist_id"],
                    "checklist_readiness_status": eligibility["checklist_readiness_status"],
                    "checklist_readiness_evidence_id": eligibility["checklist_readiness_evidence_id"],
                    "evidence_id": evidence.id,
                    "status": READY_FOR_CUTOVER_STATUS,
                    **catalog_context,
                },
                sort_keys=True,
            ),
        )
    )
    db.add(
        DomainEvent(
            event_type="load_plan.cutover_handoff.committed",
            source_module="load_plan",
            project_id=package.project_id,
            aggregate_type="load_plan_cutover_handoff",
            aggregate_id=handoff.id,
            payload_json=json.dumps(
                {
                    "package_id": package.id,
                    "status": READY_FOR_CUTOVER_STATUS,
                    "checklist_id": eligibility["checklist_id"],
                    "checklist_readiness_status": eligibility["checklist_readiness_status"],
                    "checklist_readiness_evidence_id": eligibility["checklist_readiness_evidence_id"],
                    **catalog_context,
                },
                sort_keys=True,
            ),
            status="PENDING",
        )
    )
    package.status = READY_FOR_CUTOVER_STATUS
    db.commit()
    db.refresh(handoff)
    return handoff
