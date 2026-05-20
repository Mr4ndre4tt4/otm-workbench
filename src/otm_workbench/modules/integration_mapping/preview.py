import json
from pathlib import Path

from sqlalchemy.orm import Session

from otm_workbench.models import (
    Artifact,
    IntegrationDefinition,
    IntegrationJoinRule,
    IntegrationLookupDefinition,
    IntegrationLoopDefinition,
    IntegrationMapping,
    Job,
    utcnow,
)
from otm_workbench.modules.rates.exports import file_sha256, utc_timestamp
from otm_workbench.platform.jobs import audit_job, dumps_limited_json_object, emit_job_event


SOURCE_MODULE = "integration_mapping"
PREVIEW_JOB_TYPE = "INTEGRATION_MAPPING_PREVIEW"


def preview_counts(db: Session, definition_id: str) -> dict[str, int]:
    return {
        "mappings": db.query(IntegrationMapping).filter(IntegrationMapping.definition_id == definition_id).count(),
        "loops": db.query(IntegrationLoopDefinition).filter(IntegrationLoopDefinition.definition_id == definition_id).count(),
        "joins": db.query(IntegrationJoinRule).filter(IntegrationJoinRule.definition_id == definition_id).count(),
        "lookups": db.query(IntegrationLookupDefinition)
        .filter(IntegrationLookupDefinition.definition_id == definition_id)
        .count(),
    }


def build_preview_payload(
    *,
    definition: IntegrationDefinition,
    validation: dict[str, object],
    counts: dict[str, int],
) -> dict[str, object]:
    return {
        "definition_id": definition.id,
        "definition_code": definition.code,
        "preview": {
            "mode": "synthetic_metadata_only",
            "external_calls_executed": False,
            "scenario": {
                "code": "planned_shipment_to_external_delivery",
                "source_object": "OTM PlannedShipment",
                "target_object": "External Delivery JSON",
                "payload_policy": "metadata_only_no_external_calls",
            },
            "entity_counts": counts,
            "sample_result": {
                "status": "generated_from_metadata",
                "records_previewed": 1,
            },
        },
        "validation": validation,
    }


def create_preview_artifact(
    db: Session,
    *,
    definition: IntegrationDefinition,
    artifact_root: Path,
    payload: dict[str, object],
) -> Artifact:
    export_dir = artifact_root / "integration_mapping" / definition.id / "previews" / utc_timestamp()
    export_dir.mkdir(parents=True, exist_ok=True)
    file_name = "integration_preview.json"
    file_path = export_dir / file_name
    file_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    digest, size = file_sha256(file_path)
    artifact = Artifact(
        source_module=SOURCE_MODULE,
        artifact_type="integration_preview",
        file_path=str(file_path),
        file_name=file_name,
        content_type="application/json",
        sha256=digest,
        size_bytes=size,
        sensitivity_level="internal",
    )
    db.add(artifact)
    db.flush()
    return artifact


def record_completed_preview_job(
    db: Session,
    *,
    definition: IntegrationDefinition,
    artifact: Artifact,
    result_payload: dict[str, object],
    created_by: str,
) -> Job:
    job = Job(
        job_type=PREVIEW_JOB_TYPE,
        source_module=SOURCE_MODULE,
        status="PENDING",
        progress=0,
        message="Job created.",
        input_json=dumps_limited_json_object({"definition_id": definition.id}, label="input"),
        result_json="{}",
        error_details_json="{}",
        created_by=created_by,
    )
    db.add(job)
    db.flush()
    emit_job_event(
        db,
        job=job,
        event_type="JOB_CREATED",
        status_before=None,
        status_after="PENDING",
        message="Job created.",
        created_by=created_by,
    )
    audit_job(db, actor=created_by, action="job.create", job=job)
    db.flush()

    job.status = "RUNNING"
    job.progress = 1
    job.message = "Job started."
    job.started_at = utcnow()
    emit_job_event(
        db,
        job=job,
        event_type="JOB_STARTED",
        status_before="PENDING",
        status_after="RUNNING",
        message="Job started.",
        created_by=created_by,
    )
    db.flush()

    job.status = "SUCCEEDED"
    job.progress = 100
    job.message = "Integration Mapping preview generated."
    job.result_json = dumps_limited_json_object(
        {
            "definition_id": definition.id,
            "artifact_id": artifact.id,
            "preview": result_payload["preview"],
            "validation": result_payload["validation"],
        },
        label="result",
    )
    job.finished_at = utcnow()
    emit_job_event(
        db,
        job=job,
        event_type="JOB_SUCCEEDED",
        status_before="RUNNING",
        status_after="SUCCEEDED",
        message="Integration Mapping preview generated.",
        created_by=created_by,
        payload={"artifact_id": artifact.id},
    )
    audit_job(db, actor=created_by, action="job.succeed", job=job, metadata={"artifact_id": artifact.id})
    db.flush()
    return job


def build_integration_preview(
    db: Session,
    *,
    definition: IntegrationDefinition,
    validation: dict[str, object],
    artifact_root: Path,
    created_by: str,
) -> dict[str, object]:
    counts = preview_counts(db, definition.id)
    preview_payload = build_preview_payload(definition=definition, validation=validation, counts=counts)
    artifact = create_preview_artifact(db, definition=definition, artifact_root=artifact_root, payload=preview_payload)
    job = record_completed_preview_job(
        db,
        definition=definition,
        artifact=artifact,
        result_payload=preview_payload,
        created_by=created_by,
    )
    db.commit()
    db.refresh(job)
    db.refresh(artifact)
    return {
        "definition_id": definition.id,
        "status": job.status,
        "job_id": job.id,
        "artifact_id": artifact.id,
        "preview": preview_payload["preview"],
        "validation": validation,
    }
