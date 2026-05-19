import csv
from dataclasses import dataclass
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
    LoadPlanPackage,
    LoadPlanZipAnalysis,
    Manifest,
    utcnow,
)
from otm_workbench.modules.load_plan.packages import parse_json_list, parse_json_object
from otm_workbench.modules.rates.exports import iso_now


ALTER_SESSION_LINE = "exec alter session set nls_date_format = 'YYYY-MM-DD HH24:MI:SS'"


@dataclass(frozen=True)
class DictionaryTable:
    table_name: str
    columns: dict[str, str]


def serialize_zip_analysis(analysis: LoadPlanZipAnalysis) -> dict[str, object]:
    return {
        "id": analysis.id,
        "project_id": analysis.project_id,
        "environment_id": analysis.environment_id,
        "profile_id": analysis.profile_id,
        "package_id": analysis.package_id,
        "status": analysis.status,
        "source_artifact_id": analysis.source_artifact_id,
        "source_manifest_id": analysis.source_manifest_id,
        "manifest_id": analysis.manifest_id,
        "evidence_id": analysis.evidence_id,
        "summary": parse_json_object(analysis.summary_json),
        "findings": parse_json_list(analysis.findings_json),
        "created_by": analysis.created_by,
        "analyzed_at": analysis.analyzed_at.isoformat() if analysis.analyzed_at else None,
    }


def finding(
    severity: str,
    code: str,
    message: str,
    *,
    table_name: str | None = None,
    file_name: str | None = None,
    details: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "severity": severity,
        "code": code,
        "message": message,
        "table_name": table_name,
        "file_name": file_name,
        "details": details or {},
    }


def load_dictionary_table(dictionary_root: Path, table_name: str) -> DictionaryTable | None:
    for path in (dictionary_root / f"{table_name.upper()}.json", dictionary_root / f"{table_name.lower()}.json"):
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
            columns = {
                str(column["name"]).upper(): str(column.get("dataType", "")).upper()
                for column in payload.get("columns", [])
            }
            return DictionaryTable(table_name=table_name.upper(), columns=columns)
    return None


def ensure_analyzable_package(db: Session, package: LoadPlanPackage) -> tuple[Artifact, list[dict[str, object]]]:
    if package.status != "REGISTERED":
        raise ValueError("Load Plan package must be REGISTERED before ZIP analysis.")
    if not package.artifact_id or not package.manifest_id:
        raise ValueError("Load Plan package must reference source artifact and manifest before ZIP analysis.")
    load_sequence = parse_json_list(package.load_sequence_json)
    if not load_sequence:
        raise ValueError("Load Plan package must have a load sequence before ZIP analysis.")
    artifact = db.query(Artifact).filter(Artifact.id == package.artifact_id).first()
    if artifact is None:
        raise ValueError("Load Plan package source artifact was not found.")
    artifact_path = Path(artifact.file_path)
    if not artifact_path.exists() or not zipfile.is_zipfile(artifact_path):
        raise ValueError("Load Plan package artifact must be a readable ZIP.")
    return artifact, load_sequence


def catalog_context_for_package(package: LoadPlanPackage) -> dict[str, object]:
    summary = parse_json_object(package.summary_json)
    return {
        key: summary[key]
        for key in ("catalog_macro_object_code", "catalog_load_plan_path")
        if summary.get(key)
    }


def read_csv_header(lines: list[str]) -> list[str]:
    if len(lines) < 2:
        return []
    return [column.strip().upper() for column in next(csv.reader([lines[1]]))]


def analyze_csv_member(
    *,
    archive: zipfile.ZipFile,
    member_name: str,
    dictionary_root: Path,
    load_sequence_tables: set[str],
    expected_rows_by_table: dict[str, int],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    raw = archive.read(member_name)
    text = raw.decode("utf-8-sig")
    lines = text.splitlines()
    findings: list[dict[str, object]] = []
    table_name = lines[0].strip().upper() if lines else ""
    header = read_csv_header(lines)
    has_alter_session = len(lines) >= 3 and lines[2].strip() == ALTER_SESSION_LINE
    data_start = 3 if has_alter_session else 2
    row_count = max(0, len(lines) - data_start)

    if not table_name:
        findings.append(finding("ERROR", "CSV_TABLE_LINE_MISSING", "CSV table name line is missing.", file_name=member_name))
    if not header:
        findings.append(
            finding(
                "ERROR",
                "CSV_HEADER_LINE_MISSING",
                "CSV header line is missing.",
                table_name=table_name or None,
                file_name=member_name,
            )
        )
    if table_name and table_name not in load_sequence_tables:
        findings.append(
            finding(
                "WARNING",
                "CSV_TABLE_NOT_IN_LOAD_SEQUENCE",
                "CSV table is not present in package load sequence.",
                table_name=table_name,
                file_name=member_name,
            )
        )

    dictionary_table = load_dictionary_table(dictionary_root, table_name) if table_name else None
    if table_name and dictionary_table is None:
        findings.append(
            finding(
                "ERROR",
                "CSV_TABLE_NOT_IN_DATA_DICTIONARY",
                "CSV table is not present in the Data Dictionary.",
                table_name=table_name,
                file_name=member_name,
            )
        )
    elif dictionary_table is not None:
        for column in [column for column in header if column not in dictionary_table.columns]:
            findings.append(
                finding(
                    "ERROR",
                    "CSV_UNKNOWN_COLUMN",
                    "CSV column is not present in the Data Dictionary table.",
                    table_name=table_name,
                    file_name=member_name,
                    details={"column_name": column},
                )
            )
        has_date_column = any(dictionary_table.columns.get(column) == "DATE" for column in header)
        if has_date_column and not has_alter_session:
            findings.append(
                finding(
                    "ERROR",
                    "CSV_DATE_ALTER_SESSION_MISSING",
                    "CSV includes DATE columns but does not declare the expected NLS date format.",
                    table_name=table_name,
                    file_name=member_name,
                )
            )

    expected_rows = expected_rows_by_table.get(table_name)
    if expected_rows is not None and expected_rows != row_count:
        findings.append(
            finding(
                "WARNING",
                "CSV_ROW_COUNT_MISMATCH",
                "CSV row count does not match package load sequence row count.",
                table_name=table_name,
                file_name=member_name,
                details={"expected_row_count": expected_rows, "actual_row_count": row_count},
            )
        )

    return {
        "file_name": member_name,
        "table_name": table_name,
        "row_count": row_count,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size_bytes": len(raw),
        "column_count": len(header),
        "has_alter_session": has_alter_session,
    }, findings


def generate_zip_analysis(
    db: Session,
    *,
    package: LoadPlanPackage,
    dictionary_root: Path,
    analyzed_by: str,
) -> LoadPlanZipAnalysis:
    artifact, load_sequence = ensure_analyzable_package(db, package)
    catalog_context = catalog_context_for_package(package)
    load_sequence_tables = {str(item["table_name"]).upper() for item in load_sequence}
    expected_rows_by_table = {str(item["table_name"]).upper(): int(item.get("row_count", 0)) for item in load_sequence}
    files: list[dict[str, object]] = []
    findings: list[dict[str, object]] = []
    analyzed_at = iso_now()

    with zipfile.ZipFile(artifact.file_path) as archive:
        names = archive.namelist()
        zip_file_count = len(names)
        if "manifest.json" not in names:
            findings.append(finding("WARNING", "ZIP_MANIFEST_MISSING", "ZIP does not include manifest.json."))
        csv_names = sorted(name for name in names if name.startswith("csv/") and name.lower().endswith(".csv"))
        if not csv_names:
            findings.append(finding("ERROR", "ZIP_CSV_MISSING", "ZIP does not include CSV files under csv/."))
        for csv_name in csv_names:
            file_summary, csv_findings = analyze_csv_member(
                archive=archive,
                member_name=csv_name,
                dictionary_root=dictionary_root,
                load_sequence_tables=load_sequence_tables,
                expected_rows_by_table=expected_rows_by_table,
            )
            files.append(file_summary)
            findings.extend(csv_findings)

    error_count = sum(1 for item in findings if item["severity"] == "ERROR")
    warning_count = sum(1 for item in findings if item["severity"] == "WARNING")
    summary = {
        "package_id": package.id,
        "source_module": package.source_module,
        "source_entity_type": package.source_entity_type,
        "source_entity_id": package.source_entity_id,
        "package_type": package.package_type,
        "file_count": zip_file_count,
        "csv_file_count": len(files),
        "table_count": len({str(item.get("table_name")) for item in files if item.get("table_name")}),
        "row_count": sum(int(item.get("row_count", 0)) for item in files),
        "finding_count": len(findings),
        "error_count": error_count,
        "warning_count": warning_count,
        **catalog_context,
    }
    manifest_payload = {
        "schema_version": "load-plan-zip-analysis-manifest/v1",
        "manifest_type": "zip_analysis",
        "source_module": "load_plan",
        "source_entity_type": "load_plan_package",
        "source_entity_id": package.id,
        "package": {
            "id": package.id,
            "source_module": package.source_module,
            "source_entity_id": package.source_entity_id,
            "package_type": package.package_type,
            **catalog_context,
        },
        "source_artifact": {
            "artifact_id": artifact.id,
            "file_name": artifact.file_name,
            "sha256": artifact.sha256,
            "size_bytes": artifact.size_bytes,
        },
        "files": files,
        "summary": summary,
        "findings": findings,
        "analyzed_at": analyzed_at,
        "analyzed_by": analyzed_by,
    }
    manifest = Manifest(
        project_id=package.project_id,
        source_module="load_plan",
        status="CREATED",
        manifest_json=json.dumps(manifest_payload, indent=2, sort_keys=True),
    )
    db.add(manifest)
    db.flush()

    analysis = LoadPlanZipAnalysis(
        project_id=package.project_id,
        environment_id=package.environment_id,
        profile_id=package.profile_id,
        package_id=package.id,
        status="ANALYZED",
        source_artifact_id=artifact.id,
        source_manifest_id=package.manifest_id,
        manifest_id=manifest.id,
        summary_json=json.dumps(summary, sort_keys=True),
        findings_json=json.dumps(findings, sort_keys=True),
        created_by=analyzed_by,
        analyzed_at=utcnow(),
    )
    db.add(analysis)
    db.flush()

    evidence_summary = {
        "source_entity_type": "load_plan_zip_analysis",
        "source_entity_id": analysis.id,
        "package_id": package.id,
        "source_artifact_id": artifact.id,
        "source_manifest_id": package.manifest_id,
        "manifest_id": manifest.id,
        "status": "ANALYZED",
        "csv_file_count": summary["csv_file_count"],
        "table_count": summary["table_count"],
        "row_count": summary["row_count"],
        "finding_count": summary["finding_count"],
        "error_count": summary["error_count"],
        "warning_count": summary["warning_count"],
        **catalog_context,
    }
    evidence = Evidence(
        project_id=package.project_id,
        source_module="load_plan",
        evidence_type="load_plan_zip_analysis",
        summary_json=json.dumps(evidence_summary, sort_keys=True),
        artifact_id=artifact.id,
        manifest_id=manifest.id,
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db.add(evidence)
    db.flush()

    analysis.evidence_id = evidence.id
    db.add(
        AuditLog(
            actor_user_id=analyzed_by,
            action="load_plan.zip_analysis.run",
            target_type="load_plan_zip_analysis",
            target_id=analysis.id,
            metadata_json=json.dumps(
                {
                    "package_id": package.id,
                    "source_artifact_id": artifact.id,
                    "manifest_id": manifest.id,
                    "evidence_id": evidence.id,
                    "finding_count": summary["finding_count"],
                },
                sort_keys=True,
            ),
        )
    )
    db.add(
        DomainEvent(
            event_type="load_plan.zip_analysis.completed",
            source_module="load_plan",
            project_id=package.project_id,
            aggregate_type="load_plan_zip_analysis",
            aggregate_id=analysis.id,
            payload_json=json.dumps({"package_id": package.id, "status": "ANALYZED"}, sort_keys=True),
            status="PENDING",
        )
    )
    db.commit()
    db.refresh(analysis)
    return analysis
