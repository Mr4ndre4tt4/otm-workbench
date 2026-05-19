import json

from sqlalchemy.orm import Session

from otm_workbench.models import (
    AuditLog,
    DomainEvent,
    Evidence,
    LoadPlanPackage,
    RateBatch,
    RateBatchTable,
    utcnow,
)
from otm_workbench.modules.rates.approval import get_existing_approval_evidence
from otm_workbench.modules.rates.exports import list_batch_export_evidence
from otm_workbench.modules.rates.scenarios import get_rate_scenario


def parse_json_object(value: str | None) -> dict[str, object]:
    if not value:
        return {}
    parsed = json.loads(value)
    return parsed if isinstance(parsed, dict) else {}


def parse_json_list(value: str | None) -> list[dict[str, object]]:
    if not value:
        return []
    parsed = json.loads(value)
    return parsed if isinstance(parsed, list) else []


def serialize_load_plan_package(package: LoadPlanPackage) -> dict[str, object]:
    return {
        "id": package.id,
        "project_id": package.project_id,
        "environment_id": package.environment_id,
        "profile_id": package.profile_id,
        "source_module": package.source_module,
        "source_entity_type": package.source_entity_type,
        "source_entity_id": package.source_entity_id,
        "package_type": package.package_type,
        "status": package.status,
        "artifact_id": package.artifact_id,
        "manifest_id": package.manifest_id,
        "evidence_id": package.evidence_id,
        "approval_evidence_id": package.approval_evidence_id,
        "load_sequence": parse_json_list(package.load_sequence_json),
        "summary": parse_json_object(package.summary_json),
        "created_by": package.created_by,
        "registered_at": package.registered_at.isoformat() if package.registered_at else None,
    }


def existing_rates_package(db: Session, batch_id: str) -> LoadPlanPackage | None:
    return (
        db.query(LoadPlanPackage)
        .filter(LoadPlanPackage.source_module == "rates")
        .filter(LoadPlanPackage.source_entity_type == "rate_batch")
        .filter(LoadPlanPackage.source_entity_id == batch_id)
        .order_by(LoadPlanPackage.created_at.desc())
        .first()
    )


def latest_rates_export_evidence(db: Session, batch_id: str) -> Evidence | None:
    export_evidence = list_batch_export_evidence(db, batch_id)
    if not export_evidence:
        return None
    latest = export_evidence[0]
    if not latest.artifact_id or not latest.manifest_id:
        return None
    return latest


def load_sequence_for_batch(db: Session, batch_id: str) -> list[dict[str, object]]:
    tables = (
        db.query(RateBatchTable)
        .filter(RateBatchTable.batch_id == batch_id)
        .order_by(RateBatchTable.sequence_index)
        .all()
    )
    return [
        {
            "position": table.sequence_index,
            "table_name": table.table_name,
            "row_count": table.row_count,
            "requirement_level": table.requirement_level,
        }
        for table in tables
    ]


def register_rates_package(db: Session, *, batch: RateBatch, created_by: str) -> LoadPlanPackage:
    existing = existing_rates_package(db, batch.id)
    if existing:
        return existing
    if batch.status != "APPROVED":
        raise ValueError("Rate batch must be approved before Load Plan package intake.")

    export_evidence = latest_rates_export_evidence(db, batch.id)
    if export_evidence is None:
        raise ValueError("Rate batch must have a CSV export artifact before Load Plan package intake.")

    approval_evidence = get_existing_approval_evidence(db, batch.id)
    if approval_evidence is None:
        raise ValueError("Rate batch must have approval evidence before Load Plan package intake.")

    load_sequence = load_sequence_for_batch(db, batch.id)
    scenario = get_rate_scenario(batch.scenario_code)
    catalog_context = {
        "catalog_macro_object_code": scenario.catalog_macro_object_code,
        "catalog_load_plan_path": scenario.catalog_load_plan_path,
    }
    table_count = len(load_sequence)
    row_count = sum(int(item["row_count"]) for item in load_sequence)
    if table_count == 0 or row_count == 0:
        raise ValueError("Rate batch must have tables and rows before Load Plan package intake.")

    summary = {
        "source_module": "rates",
        "source_batch_id": batch.id,
        "scenario_code": batch.scenario_code,
        **catalog_context,
        "domain_name": batch.domain_name,
        "source_status": batch.status,
        "package_type": "rates_csv_zip",
        "table_count": table_count,
        "row_count": row_count,
        "has_export_artifact": True,
        "has_approval_evidence": True,
    }
    package = LoadPlanPackage(
        project_id=batch.project_id,
        environment_id=batch.environment_id,
        profile_id=batch.profile_id,
        source_module="rates",
        source_entity_type="rate_batch",
        source_entity_id=batch.id,
        package_type="rates_csv_zip",
        status="REGISTERED",
        artifact_id=export_evidence.artifact_id,
        manifest_id=export_evidence.manifest_id,
        approval_evidence_id=approval_evidence.id,
        load_sequence_json=json.dumps(load_sequence, sort_keys=True),
        summary_json=json.dumps(summary, sort_keys=True),
        created_by=created_by,
        registered_at=utcnow(),
    )
    db.add(package)
    db.flush()

    evidence_summary = {
        "source_entity_type": "load_plan_package",
        "source_entity_id": package.id,
        "upstream_source_module": "rates",
        "upstream_entity_type": "rate_batch",
        "upstream_entity_id": batch.id,
        **catalog_context,
        "package_type": "rates_csv_zip",
        "artifact_id": export_evidence.artifact_id,
        "manifest_id": export_evidence.manifest_id,
        "approval_evidence_id": approval_evidence.id,
        "table_count": table_count,
        "row_count": row_count,
    }
    intake_evidence = Evidence(
        project_id=batch.project_id,
        source_module="load_plan",
        evidence_type="load_plan_package_intake",
        summary_json=json.dumps(evidence_summary, sort_keys=True),
        artifact_id=export_evidence.artifact_id,
        manifest_id=export_evidence.manifest_id,
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db.add(intake_evidence)
    db.flush()

    package.evidence_id = intake_evidence.id
    db.add(
        AuditLog(
            actor_user_id=created_by,
            action="load_plan.package.register_from_rates",
            target_type="load_plan_package",
            target_id=package.id,
            metadata_json=json.dumps(
                {
                    "source_module": "rates",
                    "source_entity_id": batch.id,
                    "artifact_id": export_evidence.artifact_id,
                    "manifest_id": export_evidence.manifest_id,
                    "evidence_id": intake_evidence.id,
                    **catalog_context,
                },
                sort_keys=True,
            ),
        )
    )
    db.add(
        DomainEvent(
            event_type="load_plan.package.registered",
            source_module="load_plan",
            project_id=batch.project_id,
            aggregate_type="load_plan_package",
            aggregate_id=package.id,
            payload_json=json.dumps(
                {
                    "source_module": "rates",
                    "source_entity_id": batch.id,
                    "package_type": "rates_csv_zip",
                    "status": "REGISTERED",
                    **catalog_context,
                },
                sort_keys=True,
            ),
            status="PENDING",
        )
    )
    db.commit()
    db.refresh(package)
    return package


def load_plan_package_summary(db: Session) -> dict[str, object]:
    packages = db.query(LoadPlanPackage).all()
    by_source_module: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for package in packages:
        by_source_module[package.source_module] = by_source_module.get(package.source_module, 0) + 1
        by_status[package.status] = by_status.get(package.status, 0) + 1
    return {
        "registered_packages": len(packages),
        "by_source_module": by_source_module,
        "by_status": by_status,
        "next_actions": ["build_csvutil"] if packages else [],
    }
