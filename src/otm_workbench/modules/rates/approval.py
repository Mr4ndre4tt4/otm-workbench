from dataclasses import asdict, dataclass
import json

from sqlalchemy.orm import Session

from otm_workbench.models import (
    AuditLog,
    DomainEvent,
    Evidence,
    RateBatch,
    RateBatchIssue,
    RateBatchTable,
    utcnow,
)
from otm_workbench.modules.rates.exports import list_batch_export_artifacts, list_batch_export_evidence
from otm_workbench.modules.rates.scenarios import get_rate_scenario


@dataclass(frozen=True)
class RateBatchReadiness:
    batch_id: str
    status: str
    ready_for_approval: bool
    ready_for_export: bool
    issue_summary: dict[str, int]
    table_count: int
    row_count: int
    has_export_artifact: bool
    blockers: list[str]
    next_actions: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def get_rate_batch_issue_summary(db: Session, batch_id: str) -> dict[str, int]:
    issues = db.query(RateBatchIssue).filter(RateBatchIssue.batch_id == batch_id).all()
    return {
        "errors": sum(1 for issue in issues if issue.severity == "ERROR"),
        "warnings": sum(1 for issue in issues if issue.severity == "WARNING"),
        "infos": sum(1 for issue in issues if issue.severity == "INFO"),
    }


def get_rate_batch_table_counts(db: Session, batch_id: str) -> tuple[int, int]:
    tables = db.query(RateBatchTable).filter(RateBatchTable.batch_id == batch_id).all()
    return len(tables), sum(table.row_count for table in tables)


def get_rate_batch_readiness(db: Session, batch: RateBatch) -> RateBatchReadiness:
    issue_summary = get_rate_batch_issue_summary(db, batch.id)
    table_count, row_count = get_rate_batch_table_counts(db, batch.id)
    has_export_artifact = bool(list_batch_export_artifacts(db, batch.id))
    blockers: list[str] = []

    if batch.status == "DRAFT":
        blockers.append("BATCH_NOT_VALIDATED")
    if issue_summary["errors"] > 0:
        blockers.append("HAS_ERROR_ISSUES")
    if table_count == 0:
        blockers.append("NO_TABLES")
    if row_count == 0:
        blockers.append("NO_ROWS")
    if batch.status == "APPROVED":
        blockers.append("ALREADY_APPROVED")

    approval_candidate_statuses = {"VALIDATED", "EXPORT_PREVIEWED", "EXPORTED"}
    export_candidate_statuses = {"VALIDATED", "EXPORT_PREVIEWED", "EXPORTED", "APPROVED"}
    has_minimum_content = table_count > 0 and row_count > 0
    ready_for_approval = (
        batch.status in approval_candidate_statuses and issue_summary["errors"] == 0 and has_minimum_content
    )
    ready_for_export = batch.status in export_candidate_statuses and issue_summary["errors"] == 0 and has_minimum_content

    next_actions: list[str] = []
    if ready_for_export and not has_export_artifact:
        next_actions.append("export_csv")
    if ready_for_approval:
        next_actions.append("approve")

    return RateBatchReadiness(
        batch_id=batch.id,
        status=batch.status,
        ready_for_approval=ready_for_approval,
        ready_for_export=ready_for_export,
        issue_summary=issue_summary,
        table_count=table_count,
        row_count=row_count,
        has_export_artifact=has_export_artifact,
        blockers=blockers,
        next_actions=next_actions,
    )


def get_existing_approval_evidence(db: Session, batch_id: str) -> Evidence | None:
    needle = f'"source_entity_id": "{batch_id}"'
    return (
        db.query(Evidence)
        .filter(Evidence.source_module == "rates")
        .filter(Evidence.evidence_type == "rates_batch_approval")
        .filter(Evidence.summary_json.contains(needle))
        .order_by(Evidence.created_at.desc())
        .first()
    )


def get_latest_export_references(db: Session, batch_id: str) -> tuple[str | None, str | None]:
    export_evidence = list_batch_export_evidence(db, batch_id)
    if not export_evidence:
        return None, None
    latest = export_evidence[0]
    return latest.artifact_id, latest.manifest_id


def get_rate_batch_readiness_payload(db: Session, batch: RateBatch) -> dict[str, object]:
    scenario = get_rate_scenario(batch.scenario_code)
    payload = get_rate_batch_readiness(db, batch).to_dict()
    payload["catalog_macro_object_code"] = scenario.catalog_macro_object_code
    payload["catalog_load_plan_path"] = scenario.catalog_load_plan_path
    return payload


def approve_rate_batch(
    db: Session,
    *,
    batch: RateBatch,
    approved_by: str,
    approval_note: str = "",
) -> dict[str, object]:
    if batch.status == "APPROVED":
        existing = get_existing_approval_evidence(db, batch.id)
        summary = json.loads(batch.summary_json or "{}")
        approval = summary.get("approval", {})
        scenario = get_rate_scenario(batch.scenario_code)
        return {
            "batch_id": batch.id,
            "status": batch.status,
            "approved_at": approval.get("approved_at") or (batch.approved_at.isoformat() if batch.approved_at else None),
            "approved_by": approval.get("approved_by") or approved_by,
            "evidence_id": existing.id if existing else approval.get("evidence_id"),
            "catalog_macro_object_code": scenario.catalog_macro_object_code,
            "catalog_load_plan_path": scenario.catalog_load_plan_path,
            "readiness": get_rate_batch_readiness_payload(db, batch),
        }

    readiness = get_rate_batch_readiness(db, batch)
    if readiness.issue_summary["errors"] > 0:
        raise ValueError("Rate batch has ERROR issues and cannot be approved.")
    if not readiness.ready_for_approval:
        raise ValueError("Rate batch is not ready for approval.")

    approved_at = utcnow()
    scenario = get_rate_scenario(batch.scenario_code)
    catalog_context = {
        "catalog_macro_object_code": scenario.catalog_macro_object_code,
        "catalog_load_plan_path": scenario.catalog_load_plan_path,
    }
    artifact_id, manifest_id = get_latest_export_references(db, batch.id)
    evidence_summary = {
        "source_entity_type": "rate_batch",
        "source_entity_id": batch.id,
        "scenario_code": batch.scenario_code,
        "domain_name": batch.domain_name,
        "approved_by": approved_by,
        "approved_at": approved_at.isoformat(),
        "issue_summary": readiness.issue_summary,
        "table_count": readiness.table_count,
        "row_count": readiness.row_count,
        "has_export_artifact": artifact_id is not None,
        "approval_note": approval_note,
        **catalog_context,
    }
    evidence = Evidence(
        project_id=batch.project_id,
        source_module="rates",
        evidence_type="rates_batch_approval",
        summary_json=json.dumps(evidence_summary, sort_keys=True),
        artifact_id=artifact_id,
        manifest_id=manifest_id,
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db.add(evidence)
    db.flush()

    db.add(
        AuditLog(
            actor_user_id=approved_by,
            action="rates.batch.approve",
            target_type="rate_batch",
            target_id=batch.id,
            metadata_json=json.dumps(
                {
                    "evidence_id": evidence.id,
                    "approved_by": approved_by,
                    "issue_summary": readiness.issue_summary,
                    **catalog_context,
                },
                sort_keys=True,
            ),
        )
    )
    db.add(
        DomainEvent(
            event_type="rates.batch.approved",
            source_module="rates",
            project_id=batch.project_id,
            aggregate_type="rate_batch",
            aggregate_id=batch.id,
            payload_json=json.dumps(
                {
                    "evidence_id": evidence.id,
                    "approved_by": approved_by,
                    "status": "APPROVED",
                    **catalog_context,
                },
                sort_keys=True,
            ),
            status="PENDING",
        )
    )

    summary = json.loads(batch.summary_json or "{}")
    summary["approval"] = {
        "approved_by": approved_by,
        "approved_at": approved_at.isoformat(),
        "approval_note": approval_note,
        "evidence_id": evidence.id,
        **catalog_context,
    }
    batch.status = "APPROVED"
    batch.approved_at = approved_at
    batch.summary_json = json.dumps(summary, sort_keys=True)
    db.commit()

    return {
        "batch_id": batch.id,
        "status": batch.status,
        "approved_at": approved_at.isoformat(),
        "approved_by": approved_by,
        "evidence_id": evidence.id,
        **catalog_context,
        "readiness": get_rate_batch_readiness_payload(db, batch),
    }
