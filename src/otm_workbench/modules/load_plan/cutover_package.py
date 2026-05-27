import json
from pathlib import Path
import zipfile

from sqlalchemy.orm import Session

from otm_workbench.models import (
    Artifact,
    AuditLog,
    CsvutilBuild,
    CutoverChecklist,
    DomainEvent,
    Evidence,
    LoadPlanPackage,
    Manifest,
    new_id,
)
from otm_workbench.modules.load_plan.csvutil import serialize_csvutil_build
from otm_workbench.modules.load_plan.cutover_checklist import serialize_checklist
from otm_workbench.modules.load_plan.packages import parse_json_object
from otm_workbench.modules.load_plan.readiness_export import entry_metadata, json_bytes
from otm_workbench.modules.rates.exports import file_sha256, iso_now, utc_timestamp


EXPORTED_STATUS = "EXPORTED"


def latest_checklist_readiness_evidence(db: Session, checklist_id: str) -> Evidence | None:
    candidates = (
        db.query(Evidence)
        .filter(Evidence.source_module == "load_plan")
        .filter(Evidence.evidence_type == "cutover_checklist_readiness")
        .filter(Evidence.client_safe.is_(True))
        .order_by(Evidence.created_at.desc())
        .all()
    )
    for evidence in candidates:
        summary = parse_json_object(evidence.summary_json)
        if summary.get("source_entity_id") == checklist_id:
            return evidence
    return None


def readiness_payload_from_evidence(evidence: Evidence) -> dict[str, object]:
    summary = parse_json_object(evidence.summary_json)
    return {
        "evidence_id": evidence.id,
        "status": summary.get("status"),
        "summary": summary,
        "created_at": evidence.created_at.isoformat() if evidence.created_at else None,
    }


def csvutil_builds_for_checklist(db: Session, checklist: CutoverChecklist) -> list[dict[str, object]]:
    builds = (
        db.query(CsvutilBuild)
        .filter(CsvutilBuild.package_id == checklist.package_id)
        .order_by(CsvutilBuild.built_at.desc(), CsvutilBuild.created_at.desc())
        .all()
    )
    items: list[dict[str, object]] = []
    for build in builds:
        summary = parse_json_object(build.summary_json)
        if summary.get("checklist_id") != checklist.id:
            continue
        serialized = serialize_csvutil_build(build)
        items.append(
            {
                "id": serialized["id"],
                "package_id": serialized["package_id"],
                "status": serialized["status"],
                "ctl_artifact_id": serialized["ctl_artifact_id"],
                "cl_artifact_id": serialized["cl_artifact_id"],
                "manifest_id": serialized["manifest_id"],
                "evidence_id": serialized["evidence_id"],
                "summary": serialized["summary"],
                "built_at": serialized["built_at"],
            }
        )
    return items


def catalog_context_for_checklist(checklist: CutoverChecklist) -> dict[str, object]:
    summary = parse_json_object(checklist.summary_json)
    context = {
        key: summary[key]
        for key in ("catalog_macro_object_code", "catalog_load_plan_path")
        if summary.get(key)
    }
    if checklist.catalog_macro_object_code:
        context.setdefault("catalog_macro_object_code", checklist.catalog_macro_object_code)
    return context


def domain_name_for_checklist(checklist: CutoverChecklist, package: LoadPlanPackage | None = None) -> str | None:
    if package is not None and package.domain_name:
        return package.domain_name
    return None


def generate_cutover_package_export(
    db: Session,
    *,
    checklist: CutoverChecklist,
    package: LoadPlanPackage,
    artifact_root: Path,
    exported_by: str,
) -> dict[str, object]:
    readiness_evidence = latest_checklist_readiness_evidence(db, checklist.id)
    if readiness_evidence is None:
        raise ValueError("Generate Cutover Checklist readiness before exporting the cutover package.")

    timestamp = utc_timestamp()
    export_run_id = new_id()
    export_dir = artifact_root / "load_plan" / package.id / "cutover_packages" / timestamp
    export_dir.mkdir(parents=True, exist_ok=True)
    zip_path = export_dir / f"cutover_package_{checklist.id}_{export_run_id}.zip"
    generated_at = iso_now()

    checklist_payload = serialize_checklist(db, checklist)
    readiness_payload = readiness_payload_from_evidence(readiness_evidence)
    csvutil_payload = {"items": csvutil_builds_for_checklist(db, checklist)}
    catalog_context = catalog_context_for_checklist(checklist)
    summary_payload = {
        "status": EXPORTED_STATUS,
        "checklist_id": checklist.id,
        "package_id": package.id,
        "readiness_evidence_id": readiness_evidence.id,
        "readiness_status": readiness_payload["status"],
        "csvutil_build_count": len(csvutil_payload["items"]),
        "exported_at": generated_at,
        "exported_by": exported_by,
        **catalog_context,
    }

    checklist_content = json_bytes(checklist_payload)
    readiness_content = json_bytes(readiness_payload)
    csvutil_content = json_bytes(csvutil_payload)
    manifest_payload = {
        "schema_version": "cutover-package-export-manifest/v1",
        "manifest_type": "cutover_package_export",
        "source_module": "load_plan",
        "source_entity_type": "cutover_checklist",
        "source_entity_id": checklist.id,
        "checklist_id": checklist.id,
        "package_id": package.id,
        "readiness_evidence_id": readiness_evidence.id,
        "readiness_status": readiness_payload["status"],
        "csvutil_build_count": len(csvutil_payload["items"]),
        **catalog_context,
        "files": [
            entry_metadata("checklist.json", checklist_content),
            entry_metadata("checklist_readiness.json", readiness_content),
            entry_metadata("csvutil_builds.json", csvutil_content),
        ],
        "generated_at": generated_at,
        "generated_by": exported_by,
    }
    manifest_content = json_bytes(manifest_payload)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", manifest_content)
        archive.writestr("checklist.json", checklist_content)
        archive.writestr("checklist_readiness.json", readiness_content)
        archive.writestr("csvutil_builds.json", csvutil_content)

    zip_hash, zip_size = file_sha256(zip_path)
    artifact = Artifact(
        project_id=checklist.project_id,
        profile_id=checklist.profile_id,
        environment_id=checklist.environment_id,
        domain_name=domain_name_for_checklist(checklist, package),
        visibility="PROJECT",
        source_module="load_plan",
        artifact_type="cutover_package_zip",
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
        project_id=checklist.project_id,
        profile_id=checklist.profile_id,
        environment_id=checklist.environment_id,
        domain_name=domain_name_for_checklist(checklist, package),
        visibility="PROJECT",
        source_module="load_plan",
        status="CREATED",
        manifest_json=manifest_content.decode("utf-8"),
    )
    db.add(manifest)
    db.flush()

    evidence_summary = {
        "source_entity_type": "cutover_checklist",
        "source_entity_id": checklist.id,
        "checklist_id": checklist.id,
        "package_id": package.id,
        "status": EXPORTED_STATUS,
        "artifact_type": "cutover_package_zip",
        "artifact_id": artifact.id,
        "manifest_id": manifest.id,
        "readiness_evidence_id": readiness_evidence.id,
        "readiness_status": readiness_payload["status"],
        "csvutil_build_count": len(csvutil_payload["items"]),
        **catalog_context,
    }
    evidence = Evidence(
        project_id=checklist.project_id,
        profile_id=checklist.profile_id,
        environment_id=checklist.environment_id,
        domain_name=domain_name_for_checklist(checklist, package),
        visibility="PROJECT",
        source_module="load_plan",
        evidence_type="cutover_package_export",
        summary_json=json.dumps(evidence_summary, sort_keys=True),
        manifest_id=manifest.id,
        artifact_id=artifact.id,
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db.add(evidence)
    db.flush()

    audit_payload = {
        "checklist_id": checklist.id,
        "package_id": package.id,
        "artifact_id": artifact.id,
        "manifest_id": manifest.id,
        "evidence_id": evidence.id,
        "readiness_evidence_id": readiness_evidence.id,
        "readiness_status": readiness_payload["status"],
        "csvutil_build_count": len(csvutil_payload["items"]),
        **catalog_context,
    }
    db.add(
        AuditLog(
            actor_user_id=exported_by,
            action="load_plan.cutover_package.export",
            target_type="cutover_checklist",
            target_id=checklist.id,
            metadata_json=json.dumps(audit_payload, sort_keys=True),
        )
    )
    db.add(
        DomainEvent(
            event_type="load_plan.cutover_package.exported",
            source_module="load_plan",
            project_id=checklist.project_id,
            aggregate_type="cutover_checklist",
            aggregate_id=checklist.id,
            payload_json=json.dumps({"status": EXPORTED_STATUS, **audit_payload}, sort_keys=True),
            status="PENDING",
        )
    )
    db.commit()

    return {
        **summary_payload,
        "artifact_id": artifact.id,
        "manifest_id": manifest.id,
        "evidence_id": evidence.id,
        "file_name": artifact.file_name,
        "content_type": artifact.content_type,
    }
