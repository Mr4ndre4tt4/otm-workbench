from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from datetime import UTC, datetime
import zipfile

from sqlalchemy.orm import Session

from otm_workbench.models import (
    Artifact,
    AuditLog,
    Evidence,
    Manifest,
    RateBatch,
    RateBatchIssue,
    RateBatchTable,
    utcnow,
)
from otm_workbench.modules.rates.batches import get_batch_table_rows
from otm_workbench.modules.rates.csv_preview import build_otm_csv_preview
from otm_workbench.modules.rates.scenarios import get_rate_scenario


@dataclass(frozen=True)
class RatesCsvExportResult:
    batch_id: str
    status: str
    artifact_id: str
    manifest_id: str
    evidence_id: str
    file_name: str
    file_path: str
    sha256: str
    size_bytes: int
    tables: list[str]


@dataclass(frozen=True)
class RatesCsvExportBundle:
    artifact: Artifact
    evidence: Evidence
    manifest: Manifest


def ensure_exportable_batch(db: Session, batch: RateBatch) -> None:
    error_count = (
        db.query(RateBatchIssue)
        .filter(RateBatchIssue.batch_id == batch.id, RateBatchIssue.severity == "ERROR")
        .count()
    )
    if error_count:
        raise ValueError("Rate batch has ERROR issues and cannot be exported.")
    if batch.status not in {"VALIDATED", "EXPORT_PREVIEWED"}:
        raise ValueError("Rate batch must be validated before CSV export.")
    table_count = db.query(RateBatchTable).filter(RateBatchTable.batch_id == batch.id).count()
    if table_count == 0:
        raise ValueError("Rate batch has no tables to export.")


def file_sha256(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            size += len(chunk)
            digest.update(chunk)
    return digest.hexdigest(), size


def utc_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def iso_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def table_columns_from_rows(rows: list[dict[str, object]]) -> list[str]:
    columns: list[str] = []
    for row in rows:
        for column in row:
            if column not in columns:
                columns.append(column)
    return columns


def generate_rates_csv_export(
    db: Session,
    *,
    batch: RateBatch,
    dictionary_root: Path,
    artifact_root: Path,
    generated_by: str,
) -> RatesCsvExportResult:
    ensure_exportable_batch(db, batch)
    scenario = get_rate_scenario(batch.scenario_code)
    batch_tables = (
        db.query(RateBatchTable)
        .filter(RateBatchTable.batch_id == batch.id)
        .order_by(RateBatchTable.sequence_index)
        .all()
    )
    timestamp = utc_timestamp()
    export_dir = artifact_root / "rates" / batch.id / "exports" / timestamp
    export_dir.mkdir(parents=True, exist_ok=True)
    zip_path = export_dir / f"rates_batch_{batch.id}.zip"
    generated_at = iso_now()

    manifest_files = []
    csv_entries: list[tuple[str, str]] = []
    for index, batch_table in enumerate(batch_tables, start=1):
        rows = get_batch_table_rows(db, batch_table)
        columns = table_columns_from_rows(rows)
        csv_text = build_otm_csv_preview(dictionary_root, batch_table.table_name, columns, rows)
        csv_name = f"csv/{index:03d}_{batch_table.table_name}.csv"
        csv_hash = hashlib.sha256(csv_text.encode("utf-8")).hexdigest()
        csv_size = len(csv_text.encode("utf-8"))
        csv_entries.append((csv_name, csv_text))
        manifest_files.append(
            {
                "table_name": batch_table.table_name,
                "file_name": csv_name.split("/", 1)[1],
                "row_count": batch_table.row_count,
                "sha256": csv_hash,
                "size_bytes": csv_size,
            }
        )

    issues = db.query(RateBatchIssue).filter(RateBatchIssue.batch_id == batch.id).all()
    validation_summary = {
        "errors": sum(1 for issue in issues if issue.severity == "ERROR"),
        "warnings": sum(1 for issue in issues if issue.severity == "WARNING"),
        "infos": sum(1 for issue in issues if issue.severity == "INFO"),
    }
    manifest_payload = {
        "schema_version": "rates-csv-export-manifest/v1",
        "manifest_type": "rates_csv_export",
        "source_module": "rates",
        "source_entity_type": "rate_batch",
        "source_entity_id": batch.id,
        "batch": {
            "id": batch.id,
            "scenario_code": batch.scenario_code,
            "catalog_macro_object_code": scenario.catalog_macro_object_code,
            "catalog_load_plan_path": scenario.catalog_load_plan_path,
            "status": "EXPORTED",
            "domain_name": batch.domain_name,
        },
        "files": manifest_files,
        "validation_summary": validation_summary,
        "generated_at": generated_at,
        "generated_by": generated_by,
    }
    manifest_text = json.dumps(manifest_payload, indent=2, sort_keys=True)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", manifest_text)
        for csv_name, csv_text in csv_entries:
            archive.writestr(csv_name, csv_text)

    zip_hash, zip_size = file_sha256(zip_path)
    artifact = Artifact(
        project_id=batch.project_id,
        profile_id=batch.profile_id,
        environment_id=batch.environment_id,
        domain_name=batch.domain_name,
        visibility="PROJECT",
        source_module="rates",
        artifact_type="rates_csv_zip",
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
        project_id=batch.project_id,
        profile_id=batch.profile_id,
        environment_id=batch.environment_id,
        domain_name=batch.domain_name,
        visibility="PROJECT",
        source_module="rates",
        status="CREATED",
        manifest_json=manifest_text,
    )
    db.add(manifest)
    db.flush()

    summary_payload = {
        "source_entity_type": "rate_batch",
        "source_entity_id": batch.id,
        "scenario_code": batch.scenario_code,
        "catalog_macro_object_code": scenario.catalog_macro_object_code,
        "catalog_load_plan_path": scenario.catalog_load_plan_path,
        "domain_name": batch.domain_name,
        "table_count": len(batch_tables),
        "row_count": sum(table.row_count for table in batch_tables),
        "validation_summary": validation_summary,
        "artifact_type": "rates_csv_zip",
    }
    evidence = Evidence(
        project_id=batch.project_id,
        profile_id=batch.profile_id,
        environment_id=batch.environment_id,
        domain_name=batch.domain_name,
        visibility="PROJECT",
        source_module="rates",
        evidence_type="rates_csv_export",
        summary_json=json.dumps(summary_payload, sort_keys=True),
        artifact_id=artifact.id,
        manifest_id=manifest.id,
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db.add(evidence)
    db.flush()

    audit = AuditLog(
        actor_user_id=generated_by,
        action="rates.batch.export_csv",
        target_type="rate_batch",
        target_id=batch.id,
        metadata_json=json.dumps(
            {
                "artifact_id": artifact.id,
                "manifest_id": manifest.id,
                "evidence_id": evidence.id,
                "project_id": batch.project_id,
                "profile_id": batch.profile_id,
                "environment_id": batch.environment_id,
                "domain_name": batch.domain_name,
                "table_count": len(batch_tables),
            },
            sort_keys=True,
        ),
    )
    db.add(audit)

    batch.status = "EXPORTED"
    batch.exported_at = utcnow()
    db.commit()
    return RatesCsvExportResult(
        batch_id=batch.id,
        status="EXPORTED",
        artifact_id=artifact.id,
        manifest_id=manifest.id,
        evidence_id=evidence.id,
        file_name=zip_path.name,
        file_path=str(zip_path),
        sha256=zip_hash,
        size_bytes=zip_size,
        tables=[table.table_name for table in batch_tables],
    )


def list_batch_export_evidence(db: Session, batch_id: str) -> list[Evidence]:
    needle = f'"source_entity_id": "{batch_id}"'
    return (
        db.query(Evidence)
        .filter(Evidence.source_module == "rates")
        .filter(Evidence.evidence_type == "rates_csv_export")
        .filter(Evidence.summary_json.contains(needle))
        .order_by(Evidence.created_at.desc())
        .all()
    )


def list_batch_export_artifacts(db: Session, batch_id: str) -> list[Artifact]:
    evidence_items = list_batch_export_evidence(db, batch_id)
    artifact_ids = [item.artifact_id for item in evidence_items if item.artifact_id]
    if not artifact_ids:
        return []
    return (
        db.query(Artifact)
        .filter(Artifact.id.in_(artifact_ids))
        .order_by(Artifact.created_at.desc())
        .all()
    )


def latest_batch_export_bundle(db: Session, batch_id: str) -> RatesCsvExportBundle | None:
    for evidence in list_batch_export_evidence(db, batch_id):
        if not evidence.artifact_id or not evidence.manifest_id:
            continue
        artifact = db.query(Artifact).filter(Artifact.id == evidence.artifact_id).first()
        manifest = db.query(Manifest).filter(Manifest.id == evidence.manifest_id).first()
        if artifact is None or manifest is None:
            continue
        return RatesCsvExportBundle(artifact=artifact, evidence=evidence, manifest=manifest)
    return None
