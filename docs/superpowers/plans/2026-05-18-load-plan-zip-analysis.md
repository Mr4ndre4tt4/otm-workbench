# Load Plan ZIP Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add backend/API support for analyzing registered Load Plan ZIP packages and persisting client-safe analysis history.

**Architecture:** Add a `LoadPlanZipAnalysis` persistence model and migration, then implement a focused `modules/load_plan/zip_analysis.py` service that validates a registered package, inspects the linked ZIP artifact, checks CSV structure against Data Dictionary metadata, and records manifest/evidence/audit/event data. Extend the existing Load Plan router with run/list/detail endpoints.

**Tech Stack:** Python, FastAPI, SQLAlchemy ORM, Alembic, pytest, stdlib `zipfile`, stdlib `csv`, OTM Data Dictionary JSON files.

---

## File Structure

- Create `migrations/versions/a4c8e2f9b6d3_load_plan_zip_analysis.py`: create/drop `load_plan_zip_analyses`.
- Modify `src/otm_workbench/models.py`: add `LoadPlanZipAnalysis` near other Load Plan models.
- Create `src/otm_workbench/modules/load_plan/zip_analysis.py`: package validation, ZIP inspection, dictionary checks, serialization, persistence.
- Modify `src/otm_workbench/modules/load_plan/routes.py`: add request model and three ZIP Analysis endpoints.
- Create `tests/test_load_plan_zip_analysis.py`: TDD coverage for model table, happy path, findings, error handling, list/detail.
- Modify `README.md`: document the backend-only ZIP Analysis slice.

No UI, OTM execution, CSVUTIL execution, setup review decisions, or cutover readiness logic belongs in this plan.

## Shared Test Helpers

Use synthetic data only. If helpers duplicate existing test helpers, keep them local to `tests/test_load_plan_zip_analysis.py` for this slice.

```python
def create_rate_batch(client, admin_header, scenario_code="ACCESSORIAL_ONLY"):
    response = client.post(
        "/api/v1/modules/rates/batches",
        json={"scenario_code": scenario_code, "name": "Synthetic ZIP analysis batch", "domain_name": "OTM1"},
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


def add_accessorial_table(client, admin_header, batch_id, xid="ACC_COST_001", extra_fields=None):
    row = {
        "ACCESSORIAL_COST_GID": f"OTM1.{xid}",
        "ACCESSORIAL_COST_XID": xid,
    }
    if extra_fields:
        row.update(extra_fields)
    response = client.post(
        f"/api/v1/modules/rates/batches/{batch_id}/tables",
        json={"tables": [{"table_name": "ACCESSORIAL_COST", "rows": [row]}]},
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


def prepare_registered_load_plan_package(client, admin_header, extra_fields=None):
    batch = create_rate_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"], extra_fields=extra_fields)
    preview = client.post(f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview", headers=admin_header)
    assert preview.status_code == 200
    export = client.post(f"/api/v1/modules/rates/batches/{batch['id']}/export-csv", headers=admin_header)
    assert export.status_code == 200
    approval = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/approve",
        json={"approval_note": "Reviewed for synthetic ZIP analysis package"},
        headers=admin_header,
    )
    assert approval.status_code == 200
    package = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    )
    assert package.status_code == 200
    return batch, export.json(), approval.json(), package.json()
```

## Task 1: Persistence Model And Migration

**Files:**
- Modify: `src/otm_workbench/models.py`
- Create: `migrations/versions/a4c8e2f9b6d3_load_plan_zip_analysis.py`
- Test: `tests/test_load_plan_zip_analysis.py`

- [ ] **Step 1: Write failing table existence test**

Create `tests/test_load_plan_zip_analysis.py` with imports and this first test:

```python
from sqlalchemy import inspect

from otm_workbench.database import engine


def test_load_plan_zip_analyses_table_exists_after_metadata_reset():
    tables = set(inspect(engine).get_table_names())

    assert "load_plan_zip_analyses" in tables
```

- [ ] **Step 2: Run failing test**

Run:

```bash
python -m pytest tests/test_load_plan_zip_analysis.py::test_load_plan_zip_analyses_table_exists_after_metadata_reset -q
```

Expected: FAIL because `load_plan_zip_analyses` does not exist.

- [ ] **Step 3: Add ORM model**

In `src/otm_workbench/models.py`, add this class after `CsvutilBuild`:

```python
class LoadPlanZipAnalysis(Base, TimestampMixin):
    __tablename__ = "load_plan_zip_analyses"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    package_id: Mapped[str] = mapped_column(ForeignKey("load_plan_packages.id"), index=True)
    status: Mapped[str] = mapped_column(String, default="ANALYZED", index=True)
    source_artifact_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    source_manifest_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    manifest_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    evidence_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    summary_json: Mapped[str] = mapped_column(Text, default="{}")
    findings_json: Mapped[str] = mapped_column(Text, default="[]")
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
```

- [ ] **Step 4: Add Alembic migration**

Create `migrations/versions/a4c8e2f9b6d3_load_plan_zip_analysis.py`:

```python
"""load plan zip analysis

Revision ID: a4c8e2f9b6d3
Revises: e8a1c5d9f0b2
Create Date: 2026-05-18 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "a4c8e2f9b6d3"
down_revision: str | None = "e8a1c5d9f0b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "load_plan_zip_analyses",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("environment_id", sa.String(), nullable=True),
        sa.Column("profile_id", sa.String(), nullable=True),
        sa.Column("package_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("source_artifact_id", sa.String(), nullable=True),
        sa.Column("source_manifest_id", sa.String(), nullable=True),
        sa.Column("manifest_id", sa.String(), nullable=True),
        sa.Column("evidence_id", sa.String(), nullable=True),
        sa.Column("summary_json", sa.Text(), nullable=False),
        sa.Column("findings_json", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["package_id"], ["load_plan_packages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in [
        "project_id",
        "environment_id",
        "profile_id",
        "package_id",
        "status",
        "source_artifact_id",
        "source_manifest_id",
        "manifest_id",
        "evidence_id",
    ]:
        op.create_index(
            f"ix_load_plan_zip_analyses_{column}",
            "load_plan_zip_analyses",
            [column],
        )


def downgrade() -> None:
    for column in [
        "evidence_id",
        "manifest_id",
        "source_manifest_id",
        "source_artifact_id",
        "status",
        "package_id",
        "profile_id",
        "environment_id",
        "project_id",
    ]:
        op.drop_index(f"ix_load_plan_zip_analyses_{column}", table_name="load_plan_zip_analyses")
    op.drop_table("load_plan_zip_analyses")
```

- [ ] **Step 5: Run table test**

Run:

```bash
python -m pytest tests/test_load_plan_zip_analysis.py::test_load_plan_zip_analyses_table_exists_after_metadata_reset -q
```

Expected: PASS.

- [ ] **Step 6: Commit persistence**

```bash
git add src/otm_workbench/models.py migrations/versions/a4c8e2f9b6d3_load_plan_zip_analysis.py tests/test_load_plan_zip_analysis.py
git commit -m "feat: add load plan zip analysis model"
```

## Task 2: ZIP Analysis Service Happy Path

**Files:**
- Create: `src/otm_workbench/modules/load_plan/zip_analysis.py`
- Modify: `tests/test_load_plan_zip_analysis.py`

- [ ] **Step 1: Write failing happy path test**

Append imports:

```python
import json
import zipfile

from otm_workbench.models import Artifact, AuditLog, DomainEvent, Evidence, LoadPlanPackage, LoadPlanZipAnalysis, Manifest
```

Append the shared helpers from the "Shared Test Helpers" section, then add:

```python
def test_zip_analysis_succeeds_for_registered_package(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)

    response = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    analysis = db_session.query(LoadPlanZipAnalysis).filter(LoadPlanZipAnalysis.id == payload["id"]).one()
    assert payload["package_id"] == package["id"]
    assert payload["status"] == "ANALYZED"
    assert payload["source_artifact_id"] == export["artifact_id"]
    assert payload["source_manifest_id"] == export["manifest_id"]
    assert payload["summary"]["csv_file_count"] == 1
    assert payload["summary"]["table_count"] == 1
    assert payload["summary"]["row_count"] == 1
    assert payload["summary"]["error_count"] == 0
    assert payload["summary"]["warning_count"] == 0
    assert payload["findings"] == []
    assert analysis.created_by == "admin@example.com"
    assert analysis.analyzed_at is not None
```

- [ ] **Step 2: Run failing happy path test**

Run:

```bash
python -m pytest tests/test_load_plan_zip_analysis.py::test_zip_analysis_succeeds_for_registered_package -q
```

Expected: FAIL because route/service does not exist.

- [ ] **Step 3: Implement service skeleton and happy path**

Create `src/otm_workbench/modules/load_plan/zip_analysis.py`:

```python
import csv
from dataclasses import dataclass
import hashlib
import io
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
    candidates = [
        dictionary_root / f"{table_name.upper()}.json",
        dictionary_root / f"{table_name.lower()}.json",
    ]
    path = next((item for item in candidates if item.exists()), None)
    if path is None:
        matches = list(dictionary_root.glob(f"{table_name}.json"))
        path = matches[0] if matches else None
    if path is None:
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    columns = {
        str(column["name"]).upper(): str(column.get("dataType", "")).upper()
        for column in payload.get("columns", [])
    }
    return DictionaryTable(table_name=table_name.upper(), columns=columns)


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


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


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
        findings.append(finding("ERROR", "CSV_HEADER_LINE_MISSING", "CSV header line is missing.", table_name=table_name or None, file_name=member_name))
    if table_name and table_name not in load_sequence_tables:
        findings.append(finding("WARNING", "CSV_TABLE_NOT_IN_LOAD_SEQUENCE", "CSV table is not present in package load sequence.", table_name=table_name, file_name=member_name))

    dictionary_table = load_dictionary_table(dictionary_root, table_name) if table_name else None
    if table_name and dictionary_table is None:
        findings.append(finding("ERROR", "CSV_TABLE_NOT_IN_DATA_DICTIONARY", "CSV table is not present in the Data Dictionary.", table_name=table_name, file_name=member_name))
    elif dictionary_table is not None:
        unknown_columns = [column for column in header if column not in dictionary_table.columns]
        for column in unknown_columns:
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

    file_summary = {
        "file_name": member_name,
        "table_name": table_name,
        "row_count": row_count,
        "sha256": sha256_bytes(raw),
        "size_bytes": len(raw),
        "column_count": len(header),
        "has_alter_session": has_alter_session,
    }
    return file_summary, findings


def generate_zip_analysis(
    db: Session,
    *,
    package: LoadPlanPackage,
    dictionary_root: Path,
    analyzed_by: str,
) -> LoadPlanZipAnalysis:
    artifact, load_sequence = ensure_analyzable_package(db, package)
    load_sequence_tables = {str(item["table_name"]).upper() for item in load_sequence}
    expected_rows_by_table = {str(item["table_name"]).upper(): int(item.get("row_count", 0)) for item in load_sequence}
    files: list[dict[str, object]] = []
    findings: list[dict[str, object]] = []
    analyzed_at = iso_now()
    zip_file_count = 0

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
```

- [ ] **Step 4: Run service import check**

Run:

```bash
python -c "from otm_workbench.modules.load_plan.zip_analysis import generate_zip_analysis, serialize_zip_analysis; print('ok')"
```

Expected: prints `ok`.

- [ ] **Step 5: Commit service skeleton**

```bash
git add src/otm_workbench/modules/load_plan/zip_analysis.py tests/test_load_plan_zip_analysis.py
git commit -m "feat: analyze load plan zip packages"
```

## Task 3: ZIP Analysis Routes

**Files:**
- Modify: `src/otm_workbench/modules/load_plan/routes.py`
- Modify: `tests/test_load_plan_zip_analysis.py`

- [ ] **Step 1: Add route contract tests**

Append:

```python
def test_zip_analysis_creates_manifest_evidence_audit_and_event(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)

    response = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    manifest = db_session.query(Manifest).filter(Manifest.id == payload["manifest_id"]).one()
    evidence = db_session.query(Evidence).filter(Evidence.id == payload["evidence_id"]).one()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "load_plan.zip_analysis.run").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "load_plan.zip_analysis.completed").one()
    manifest_json = json.loads(manifest.manifest_json)

    assert manifest_json["manifest_type"] == "zip_analysis"
    assert manifest_json["package"]["id"] == package["id"]
    assert manifest_json["files"][0]["table_name"] == "ACCESSORIAL_COST"
    assert evidence.client_safe is True
    assert evidence.evidence_type == "load_plan_zip_analysis"
    assert evidence.artifact_id == export["artifact_id"]
    assert "OTM1.ACC_COST_001" not in evidence.summary_json
    assert "OTM1.ACC_COST_001" not in manifest.manifest_json
    assert audit.target_id == payload["id"]
    assert event.aggregate_id == payload["id"]
    assert event.status == "PENDING"


def test_zip_analysis_list_and_detail(client, admin_header):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    created = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": package["id"]},
        headers=admin_header,
    ).json()

    listed = client.get("/api/v1/modules/load-plan/zip-analysis", headers=admin_header)
    detail = client.get(f"/api/v1/modules/load-plan/zip-analysis/{created['id']}", headers=admin_header)

    assert listed.status_code == 200
    assert detail.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == created["id"]
    assert detail.json()["summary"]["package_type"] == "rates_csv_zip"
```

- [ ] **Step 2: Run failing route tests**

Run:

```bash
python -m pytest tests/test_load_plan_zip_analysis.py::test_zip_analysis_creates_manifest_evidence_audit_and_event tests/test_load_plan_zip_analysis.py::test_zip_analysis_list_and_detail -q
```

Expected: FAIL until routes import and call the service.

- [ ] **Step 3: Add routes**

In `src/otm_workbench/modules/load_plan/routes.py`, update imports:

```python
from otm_workbench.models import CsvutilBuild, LoadPlanPackage, LoadPlanZipAnalysis, RateBatch, User
from otm_workbench.modules.load_plan.zip_analysis import generate_zip_analysis, serialize_zip_analysis
```

Add request model:

```python
class ZipAnalysisRequest(BaseModel):
    package_id: str
```

Add endpoints after CSVUTIL endpoints:

```python
@router.post("/zip-analysis")
def run_zip_analysis(
    payload: ZipAnalysisRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    package = db.query(LoadPlanPackage).filter(LoadPlanPackage.id == payload.package_id).first()
    if package is None:
        raise HTTPException(status_code=404, detail="Load Plan package not found.")
    try:
        analysis = generate_zip_analysis(
            db,
            package=package,
            dictionary_root=Path(get_settings().otm_data_dictionary_root),
            analyzed_by=user.email,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize_zip_analysis(analysis)


@router.get("/zip-analysis")
def list_zip_analyses(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    analyses = db.query(LoadPlanZipAnalysis).order_by(LoadPlanZipAnalysis.created_at.desc()).all()
    items = [serialize_zip_analysis(analysis) for analysis in analyses]
    return PageResponse(items=items, total=len(items))


@router.get("/zip-analysis/{analysis_id}")
def get_zip_analysis(
    analysis_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    analysis = db.query(LoadPlanZipAnalysis).filter(LoadPlanZipAnalysis.id == analysis_id).first()
    if analysis is None:
        raise HTTPException(status_code=404, detail="ZIP analysis not found.")
    return serialize_zip_analysis(analysis)
```

- [ ] **Step 4: Run route tests**

Run:

```bash
python -m pytest tests/test_load_plan_zip_analysis.py::test_zip_analysis_succeeds_for_registered_package tests/test_load_plan_zip_analysis.py::test_zip_analysis_creates_manifest_evidence_audit_and_event tests/test_load_plan_zip_analysis.py::test_zip_analysis_list_and_detail -q
```

Expected: PASS.

- [ ] **Step 5: Commit routes**

```bash
git add src/otm_workbench/modules/load_plan/routes.py tests/test_load_plan_zip_analysis.py
git commit -m "feat: expose load plan zip analysis endpoints"
```

## Task 4: Findings And Negative Cases

**Files:**
- Modify: `tests/test_load_plan_zip_analysis.py`
- Modify: `src/otm_workbench/modules/load_plan/zip_analysis.py`

- [ ] **Step 1: Add date alter-session finding test**

Append:

```python
def test_zip_analysis_requires_alter_session_for_date_columns(client, admin_header):
    batch, export, approval, package = prepare_registered_load_plan_package(
        client,
        admin_header,
        extra_fields={"EFFECTIVE_DATE": "2026-05-18 00:00:00"},
    )

    response = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    codes = [item["code"] for item in response.json()["findings"]]
    assert "CSV_DATE_ALTER_SESSION_MISSING" not in codes
```

Expected note: generated Rates CSV should include the alter-session line for date columns, so the finding must not appear.

- [ ] **Step 2: Add unknown column finding test**

Append:

```python
def test_zip_analysis_flags_unknown_columns(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    artifact = db_session.query(Artifact).filter(Artifact.id == export["artifact_id"]).one()
    with zipfile.ZipFile(artifact.file_path, "a", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "csv/001_ACCESSORIAL_COST.csv",
            "ACCESSORIAL_COST\n"
            "ACCESSORIAL_COST_GID,ACCESSORIAL_COST_XID,SYNTHETIC_UNKNOWN_COLUMN\n"
            "OTM1.ACC_COST_001,ACC_COST_001,DEMO\n",
        )

    response = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    findings = response.json()["findings"]
    assert any(item["code"] == "CSV_UNKNOWN_COLUMN" for item in findings)
    assert "DEMO" not in json.dumps(response.json())
```

- [ ] **Step 3: Add missing and non-ZIP artifact tests**

Append:

```python
def test_zip_analysis_rejects_missing_package(client, admin_header):
    response = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": "missing_package"},
        headers=admin_header,
    )

    assert response.status_code == 404


def test_zip_analysis_rejects_missing_source_artifact(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    package_row = db_session.query(LoadPlanPackage).filter(LoadPlanPackage.id == package["id"]).one()
    package_row.artifact_id = "missing_artifact"
    db_session.commit()

    response = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "artifact" in response.json()["message"].lower()


def test_zip_analysis_rejects_non_zip_artifact(client, admin_header, db_session, tmp_path):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    text_path = tmp_path / "not_a_zip.txt"
    text_path.write_text("synthetic text artifact", encoding="utf-8")
    artifact = Artifact(
        source_module="rates",
        artifact_type="rates_csv_zip",
        file_path=str(text_path),
        file_name=text_path.name,
        content_type="text/plain",
        sha256="synthetic",
        size_bytes=text_path.stat().st_size,
        sensitivity_level="internal",
    )
    db_session.add(artifact)
    db_session.flush()
    package_row = db_session.query(LoadPlanPackage).filter(LoadPlanPackage.id == package["id"]).one()
    package_row.artifact_id = artifact.id
    db_session.commit()

    response = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "readable zip" in response.json()["message"].lower()
```

- [ ] **Step 4: Run negative/finding tests**

Run:

```bash
python -m pytest tests/test_load_plan_zip_analysis.py::test_zip_analysis_requires_alter_session_for_date_columns tests/test_load_plan_zip_analysis.py::test_zip_analysis_flags_unknown_columns tests/test_load_plan_zip_analysis.py::test_zip_analysis_rejects_missing_package tests/test_load_plan_zip_analysis.py::test_zip_analysis_rejects_missing_source_artifact tests/test_load_plan_zip_analysis.py::test_zip_analysis_rejects_non_zip_artifact -q
```

Expected: PASS after service behavior matches the tests.

- [ ] **Step 5: Commit findings and errors**

```bash
git add src/otm_workbench/modules/load_plan/zip_analysis.py tests/test_load_plan_zip_analysis.py
git commit -m "test: cover zip analysis findings and errors"
```

## Task 5: README And Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README**

Add after the Load Plan CSVUTIL Builder paragraph:

```markdown
The Load Plan ZIP Analysis slice inspects registered package ZIP artifacts,
records client-safe file/table/row counts and Data Dictionary findings, and
persists manifest/evidence/audit/event metadata without running CSVUTIL,
connecting to OTM, creating setup review decisions, or producing cutover
readiness.
```

- [ ] **Step 2: Run focused tests**

Run:

```bash
python -m pytest tests/test_load_plan_zip_analysis.py -q
```

Expected: all ZIP Analysis tests PASS.

- [ ] **Step 3: Run full verification**

Run:

```bash
python -m pytest -q
python -m alembic upgrade head
python -m ruff check src tests
```

Expected:

- pytest passes all tests.
- Alembic upgrades through `a4c8e2f9b6d3`.
- Ruff reports no issues.

- [ ] **Step 4: Commit docs**

```bash
git add README.md
git commit -m "docs: document load plan zip analysis"
```

## Final Acceptance Checklist

- [ ] `load_plan_zip_analyses` exists after metadata reset.
- [ ] ZIP Analysis can run for a registered Rates-backed Load Plan package.
- [ ] Analysis response includes source artifact/manifest ids, summary, findings, evidence id, and manifest id.
- [ ] Manifest/evidence/audit/event records are created.
- [ ] Data Dictionary checks are active for `ACCESSORIAL_COST`.
- [ ] Date CSV rule is respected.
- [ ] Unknown columns create client-safe findings.
- [ ] Missing package, missing artifact, and non-ZIP artifact errors are handled.
- [ ] Raw row values such as `OTM1.ACC_COST_001` are not persisted in analysis evidence or manifest.
- [ ] No UI, OTM execution, CSVUTIL execution, setup review decisions, or cutover readiness was added.
