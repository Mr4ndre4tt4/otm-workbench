import hashlib
import json
from pathlib import Path
import zipfile

from sqlalchemy.orm import Session

from otm_workbench.models import (
    Artifact,
    AuditLog,
    DomainEvent,
    Evidence,
    LoadPlanCutoverReadiness,
    LoadPlanReadinessExport,
    Manifest,
    new_id,
    utcnow,
)
from otm_workbench.modules.load_plan.packages import parse_json_list, parse_json_object
from otm_workbench.modules.load_plan.readiness import serialize_cutover_readiness
from otm_workbench.modules.rates.exports import file_sha256, iso_now, utc_timestamp


EXPORTED_STATUS = "EXPORTED"


def json_bytes(payload: dict[str, object] | list[dict[str, object]]) -> bytes:
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")


def entry_metadata(path: str, content: bytes) -> dict[str, object]:
    return {
        "path": path,
        "sha256": hashlib.sha256(content).hexdigest(),
        "size_bytes": len(content),
    }


def serialize_readiness_export(export: LoadPlanReadinessExport) -> dict[str, object]:
    return {
        "id": export.id,
        "project_id": export.project_id,
        "environment_id": export.environment_id,
        "profile_id": export.profile_id,
        "package_id": export.package_id,
        "readiness_id": export.readiness_id,
        "status": export.status,
        "artifact_id": export.artifact_id,
        "manifest_id": export.manifest_id,
        "evidence_id": export.evidence_id,
        "summary": parse_json_object(export.summary_json),
        "exported_by": export.exported_by,
        "exported_at": export.exported_at.isoformat() if export.exported_at else None,
    }


def catalog_context_for_readiness(readiness: LoadPlanCutoverReadiness) -> dict[str, object]:
    summary = parse_json_object(readiness.summary_json)
    return {
        key: summary[key]
        for key in ("catalog_macro_object_code", "catalog_load_plan_path")
        if summary.get(key)
    }


def generate_readiness_export(
    db: Session,
    *,
    readiness: LoadPlanCutoverReadiness,
    artifact_root: Path,
    exported_by: str,
) -> LoadPlanReadinessExport:
    timestamp = utc_timestamp()
    export_run_id = new_id()
    export_dir = artifact_root / "load_plan" / readiness.package_id / "readiness_exports" / timestamp
    export_dir.mkdir(parents=True, exist_ok=True)
    zip_path = export_dir / f"load_plan_readiness_{readiness.id}_{export_run_id}.zip"
    generated_at = iso_now()

    readiness_payload = serialize_cutover_readiness(readiness)
    blockers_payload = parse_json_list(readiness.blockers_json)
    catalog_context = catalog_context_for_readiness(readiness)
    summary_payload = {
        "source_entity_type": "load_plan_cutover_readiness",
        "source_entity_id": readiness.id,
        "package_id": readiness.package_id,
        "readiness_status": readiness.status,
        "blocker_count": len(blockers_payload),
        "exported_at": generated_at,
        "exported_by": exported_by,
        **catalog_context,
    }

    readiness_content = json_bytes(readiness_payload)
    blockers_content = json_bytes(blockers_payload)
    manifest_payload = {
        "schema_version": "load-plan-readiness-export-manifest/v1",
        "manifest_type": "load_plan_readiness_export",
        "source_module": "load_plan",
        "source_entity_type": "load_plan_cutover_readiness",
        "source_entity_id": readiness.id,
        "package_id": readiness.package_id,
        "readiness_status": readiness.status,
        **catalog_context,
        "files": [
            entry_metadata("readiness.json", readiness_content),
            entry_metadata("blockers.json", blockers_content),
        ],
        "generated_at": generated_at,
        "generated_by": exported_by,
    }
    manifest_content = json_bytes(manifest_payload)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", manifest_content)
        archive.writestr("readiness.json", readiness_content)
        archive.writestr("blockers.json", blockers_content)

    zip_hash, zip_size = file_sha256(zip_path)
    artifact = Artifact(
        project_id=readiness.project_id,
        source_module="load_plan",
        artifact_type="load_plan_readiness_export_zip",
        file_path=str(zip_path),
        file_name=zip_path.name,
        content_type="application/zip",
        sha256=zip_hash,
        size_bytes=zip_size,
        sensitivity_level="internal",
    )
    db.add(artifact)
    db.flush()

    manifest = Manifest(
        project_id=readiness.project_id,
        source_module="load_plan",
        status="CREATED",
        manifest_json=manifest_content.decode("utf-8"),
    )
    db.add(manifest)
    db.flush()

    evidence_summary = {
        "source_entity_type": "load_plan_readiness_export",
        "source_entity_id": None,
        "readiness_id": readiness.id,
        "package_id": readiness.package_id,
        "readiness_status": readiness.status,
        "artifact_type": "load_plan_readiness_export_zip",
        "blocker_count": len(blockers_payload),
        **catalog_context,
    }
    evidence = Evidence(
        project_id=readiness.project_id,
        source_module="load_plan",
        evidence_type="load_plan_readiness_export",
        summary_json=json.dumps(evidence_summary, sort_keys=True),
        manifest_id=manifest.id,
        artifact_id=artifact.id,
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db.add(evidence)
    db.flush()

    export = LoadPlanReadinessExport(
        project_id=readiness.project_id,
        environment_id=readiness.environment_id,
        profile_id=readiness.profile_id,
        package_id=readiness.package_id,
        readiness_id=readiness.id,
        status=EXPORTED_STATUS,
        artifact_id=artifact.id,
        manifest_id=manifest.id,
        evidence_id=evidence.id,
        summary_json=json.dumps(summary_payload, sort_keys=True),
        exported_by=exported_by,
        exported_at=utcnow(),
    )
    db.add(export)
    db.flush()

    evidence_summary["source_entity_id"] = export.id
    evidence.summary_json = json.dumps(evidence_summary, sort_keys=True)

    db.add(
        AuditLog(
            actor_user_id=exported_by,
            action="load_plan.readiness_export.export",
            target_type="load_plan_readiness_export",
            target_id=export.id,
            metadata_json=json.dumps(
                {
                    "readiness_id": readiness.id,
                    "package_id": readiness.package_id,
                    "artifact_id": artifact.id,
                    "manifest_id": manifest.id,
                    "evidence_id": evidence.id,
                    "readiness_status": readiness.status,
                    "blocker_count": len(blockers_payload),
                },
                sort_keys=True,
            ),
        )
    )
    db.add(
        DomainEvent(
            event_type="load_plan.readiness_export.exported",
            source_module="load_plan",
            project_id=readiness.project_id,
            aggregate_type="load_plan_readiness_export",
            aggregate_id=export.id,
            payload_json=json.dumps(
                {
                    "readiness_id": readiness.id,
                    "package_id": readiness.package_id,
                    "status": EXPORTED_STATUS,
                    "readiness_status": readiness.status,
                },
                sort_keys=True,
            ),
            status="PENDING",
        )
    )
    db.commit()
    db.refresh(export)
    return export
