# Rates CSV Export Artifacts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate durable Rates CSV ZIP artifacts from validated Rates batches, with manifest, client-safe evidence, audit log, and batch export status.

**Architecture:** Add a focused `modules/rates/exports.py` service that reads persisted batch tables/rows, reuses the Data Dictionary-backed CSV builder, writes a ZIP package under `artifact_root`, and creates platform `Artifact`, `Manifest`, `Evidence`, and `AuditLog` records in one transaction. Expose thin routes for export, batch artifacts, and batch evidence.

**Tech Stack:** Python, FastAPI, SQLAlchemy, SQLite, Alembic-free model reuse, `zipfile`, `hashlib`, pytest, Ruff.

---

## File Structure

- Create `src/otm_workbench/modules/rates/exports.py`: export service, ZIP writer, manifest builder, batch artifact/evidence lookup.
- Modify `src/otm_workbench/modules/rates/routes.py`: add `export-csv`, `artifacts`, and `evidence` endpoints.
- Create `tests/test_rates_csv_export_artifacts.py`: endpoint, ZIP, artifact, manifest, evidence, and audit tests.
- Modify `README.md`: document the Rates CSV export artifact verification command.

This slice does not require a database migration. It uses existing `Artifact`, `Manifest`, `Evidence`, `AuditLog`, and `RateBatch` models.

---

## Task 1: Export Preconditions

**Files:**
- Create: `src/otm_workbench/modules/rates/exports.py`
- Test: `tests/test_rates_csv_export_artifacts.py`

- [ ] **Step 1: Write failing precondition tests**

Create `tests/test_rates_csv_export_artifacts.py`:

```python
def create_batch(client, admin_header, scenario_code="ACCESSORIAL_ONLY"):
    return client.post(
        "/api/v1/modules/rates/batches",
        json={"scenario_code": scenario_code, "name": "Synthetic export batch", "domain_name": "OTM1"},
        headers=admin_header,
    ).json()


def add_accessorial_table(client, admin_header, batch_id):
    return client.post(
        f"/api/v1/modules/rates/batches/{batch_id}/tables",
        json={
            "tables": [
                {
                    "table_name": "ACCESSORIAL_COST",
                    "rows": [
                        {
                            "ACCESSORIAL_COST_GID": "OTM1.ACC_COST_001",
                            "ACCESSORIAL_COST_XID": "ACC_COST_001",
                            "COST_CODE_GID": "OTM1.ACC_FUEL",
                        }
                    ],
                }
            ]
        },
        headers=admin_header,
    )


def test_export_rejects_unvalidated_batch(client, admin_header):
    batch = create_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])

    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/export-csv",
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "validated" in response.json()["detail"].lower()


def test_export_rejects_batch_with_error_issues(client, admin_header):
    batch = create_batch(client, admin_header, scenario_code="RATE_GEO_ONLY")
    add_accessorial_table(client, admin_header, batch["id"])
    client.post(f"/api/v1/modules/rates/batches/{batch['id']}/validate", headers=admin_header)

    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/export-csv",
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "error" in response.json()["detail"].lower()
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/test_rates_csv_export_artifacts.py::test_export_rejects_unvalidated_batch tests/test_rates_csv_export_artifacts.py::test_export_rejects_batch_with_error_issues -q
```

Expected: FAIL with 404 because export endpoint does not exist.

- [ ] **Step 3: Create export result dataclass and precondition helper**

Create `src/otm_workbench/modules/rates/exports.py`:

```python
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from otm_workbench.models import RateBatch, RateBatchIssue, RateBatchTable


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


def ensure_exportable_batch(db: Session, batch: RateBatch) -> None:
    if batch.status not in {"VALIDATED", "EXPORT_PREVIEWED"}:
        raise ValueError("Rate batch must be validated before CSV export.")
    error_count = (
        db.query(RateBatchIssue)
        .filter(RateBatchIssue.batch_id == batch.id, RateBatchIssue.severity == "ERROR")
        .count()
    )
    if error_count:
        raise ValueError("Rate batch has ERROR issues and cannot be exported.")
    table_count = db.query(RateBatchTable).filter(RateBatchTable.batch_id == batch.id).count()
    if table_count == 0:
        raise ValueError("Rate batch has no tables to export.")
```

- [ ] **Step 4: Add a temporary route that enforces preconditions**

In `routes.py`, import `ensure_exportable_batch` and add:

```python
@router.post("/batches/{batch_id}/export-csv")
def export_rates_batch_csv(batch_id: str, db: Session = Depends(get_db), user: User = Depends(require_user)):
    batch = db.query(RateBatch).filter(RateBatch.id == batch_id).first()
    if batch is None:
        raise HTTPException(status_code=404, detail="Rate batch not found.")
    try:
        ensure_exportable_batch(db, batch)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"batch_id": batch.id, "status": batch.status}
```

- [ ] **Step 5: Run precondition tests**

Run:

```bash
python -m pytest tests/test_rates_csv_export_artifacts.py::test_export_rejects_unvalidated_batch tests/test_rates_csv_export_artifacts.py::test_export_rejects_batch_with_error_issues -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/otm_workbench/modules/rates/exports.py src/otm_workbench/modules/rates/routes.py tests/test_rates_csv_export_artifacts.py
git commit -m "feat: guard rates csv export preconditions"
```

---

## Task 2: ZIP Package Writer

**Files:**
- Modify: `src/otm_workbench/modules/rates/exports.py`
- Test: `tests/test_rates_csv_export_artifacts.py`

- [ ] **Step 1: Write failing ZIP export test**

Append to `tests/test_rates_csv_export_artifacts.py`:

```python
import json
from pathlib import Path
import zipfile


def test_export_creates_zip_with_manifest_and_csv(client, admin_header):
    batch = create_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])
    validation = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/validate",
        headers=admin_header,
    )
    assert validation.json()["valid"] is True

    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/export-csv",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    zip_path = Path(payload["file_path"])
    assert zip_path.exists()
    assert payload["file_name"].endswith(".zip")
    assert payload["tables"] == ["ACCESSORIAL_COST"]

    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        assert "manifest.json" in names
        assert "csv/001_ACCESSORIAL_COST.csv" in names
        csv_text = archive.read("csv/001_ACCESSORIAL_COST.csv").decode("utf-8")
        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))

    assert csv_text.splitlines()[0] == "ACCESSORIAL_COST"
    assert csv_text.splitlines()[1].startswith("ACCESSORIAL_COST_GID")
    assert manifest["manifest_type"] == "rates_csv_export"
    assert manifest["batch"]["id"] == batch["id"]
    assert "OTM1.ACC_COST_001" not in json.dumps(manifest)
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
python -m pytest tests/test_rates_csv_export_artifacts.py::test_export_creates_zip_with_manifest_and_csv -q
```

Expected: FAIL because export route does not create a ZIP yet.

- [ ] **Step 3: Implement ZIP helpers**

In `exports.py`, add:

```python
import hashlib
import json
from datetime import UTC, datetime
import zipfile

from otm_workbench.models import RateBatchRow
from otm_workbench.modules.rates.batches import get_batch_table_rows
from otm_workbench.modules.rates.csv_preview import build_otm_csv_preview


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
```

- [ ] **Step 4: Implement package generation skeleton**

Add `generate_rates_csv_export` in `exports.py`:

```python
def generate_rates_csv_export(
    db: Session,
    *,
    batch: RateBatch,
    dictionary_root: Path,
    artifact_root: Path,
    generated_by: str,
) -> RatesCsvExportResult:
    ensure_exportable_batch(db, batch)
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
    return RatesCsvExportResult(
        batch_id=batch.id,
        status="EXPORTED",
        artifact_id="",
        manifest_id="",
        evidence_id="",
        file_name=zip_path.name,
        file_path=str(zip_path),
        sha256=zip_hash,
        size_bytes=zip_size,
        tables=[table.table_name for table in batch_tables],
    )
```

- [ ] **Step 5: Update route to call generator**

Replace the temporary route body with:

```python
result = generate_rates_csv_export(
    db,
    batch=batch,
    dictionary_root=Path(get_settings().otm_data_dictionary_root),
    artifact_root=Path(get_settings().artifact_root),
    generated_by=user.email,
)
return result.__dict__
```

- [ ] **Step 6: Run ZIP test**

Run:

```bash
python -m pytest tests/test_rates_csv_export_artifacts.py::test_export_creates_zip_with_manifest_and_csv -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/otm_workbench/modules/rates/exports.py src/otm_workbench/modules/rates/routes.py tests/test_rates_csv_export_artifacts.py
git commit -m "feat: generate rates csv export zip"
```

---

## Task 3: Artifact, Manifest, Evidence, Audit

**Files:**
- Modify: `src/otm_workbench/modules/rates/exports.py`
- Test: `tests/test_rates_csv_export_artifacts.py`

- [ ] **Step 1: Write failing metadata test**

Append to `tests/test_rates_csv_export_artifacts.py`:

```python
from otm_workbench.models import Artifact, AuditLog, Evidence, Manifest, RateBatch


def test_export_registers_artifact_manifest_evidence_and_audit(client, admin_header, db_session):
    batch = create_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])
    client.post(f"/api/v1/modules/rates/batches/{batch['id']}/validate", headers=admin_header)

    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/export-csv",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    artifact = db_session.query(Artifact).filter(Artifact.id == payload["artifact_id"]).one()
    manifest = db_session.query(Manifest).filter(Manifest.id == payload["manifest_id"]).one()
    evidence = db_session.query(Evidence).filter(Evidence.id == payload["evidence_id"]).one()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "rates.batch.export_csv").one()
    refreshed_batch = db_session.query(RateBatch).filter(RateBatch.id == batch["id"]).one()

    assert artifact.artifact_type == "rates_csv_zip"
    assert artifact.content_type == "application/zip"
    assert artifact.sha256 == payload["sha256"]
    assert manifest.source_module == "rates"
    assert "OTM1.ACC_COST_001" not in manifest.manifest_json
    assert evidence.client_safe is True
    assert evidence.artifact_id == artifact.id
    assert evidence.manifest_id == manifest.id
    assert "OTM1.ACC_COST_001" not in evidence.summary_json
    assert audit.target_id == batch["id"]
    assert refreshed_batch.status == "EXPORTED"
    assert refreshed_batch.exported_at is not None
```

- [ ] **Step 2: Run metadata test to verify failure**

Run:

```bash
python -m pytest tests/test_rates_csv_export_artifacts.py::test_export_registers_artifact_manifest_evidence_and_audit -q
```

Expected: FAIL because IDs are blank and metadata rows are not created yet.

- [ ] **Step 3: Add metadata record creation**

In `exports.py`, import:

```python
from otm_workbench.models import Artifact, AuditLog, Evidence, Manifest, utcnow
```

After writing the ZIP and computing hash/size, create:

```python
artifact = Artifact(
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
    "domain_name": batch.domain_name,
    "table_count": len(batch_tables),
    "row_count": sum(table.row_count for table in batch_tables),
    "validation_summary": validation_summary,
    "artifact_type": "rates_csv_zip",
}
evidence = Evidence(
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
            "table_count": len(batch_tables),
        },
        sort_keys=True,
    ),
)
db.add(audit)

batch.status = "EXPORTED"
batch.exported_at = utcnow()
db.commit()
```

Return actual `artifact.id`, `manifest.id`, and `evidence.id`.

- [ ] **Step 4: Run metadata test**

Run:

```bash
python -m pytest tests/test_rates_csv_export_artifacts.py::test_export_registers_artifact_manifest_evidence_and_audit -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/otm_workbench/modules/rates/exports.py tests/test_rates_csv_export_artifacts.py
git commit -m "feat: register rates csv export evidence"
```

---

## Task 4: Batch Artifacts And Evidence Endpoints

**Files:**
- Modify: `src/otm_workbench/modules/rates/exports.py`
- Modify: `src/otm_workbench/modules/rates/routes.py`
- Test: `tests/test_rates_csv_export_artifacts.py`

- [ ] **Step 1: Write failing lookup endpoint test**

Append to `tests/test_rates_csv_export_artifacts.py`:

```python
def test_batch_artifacts_and_evidence_endpoints_return_export_records(client, admin_header):
    batch = create_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])
    client.post(f"/api/v1/modules/rates/batches/{batch['id']}/validate", headers=admin_header)
    export = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/export-csv",
        headers=admin_header,
    ).json()

    artifacts = client.get(
        f"/api/v1/modules/rates/batches/{batch['id']}/artifacts",
        headers=admin_header,
    )
    evidence = client.get(
        f"/api/v1/modules/rates/batches/{batch['id']}/evidence",
        headers=admin_header,
    )

    assert artifacts.status_code == 200
    assert evidence.status_code == 200
    assert artifacts.json()["items"][0]["id"] == export["artifact_id"]
    assert evidence.json()["items"][0]["id"] == export["evidence_id"]
    assert "OTM1.ACC_COST_001" not in str(evidence.json())
```

- [ ] **Step 2: Run lookup test to verify failure**

Run:

```bash
python -m pytest tests/test_rates_csv_export_artifacts.py::test_batch_artifacts_and_evidence_endpoints_return_export_records -q
```

Expected: FAIL with 404.

- [ ] **Step 3: Add lookup helpers**

In `exports.py`, add:

```python
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
```

- [ ] **Step 4: Add route serializers and endpoints**

In `routes.py`, import `Artifact`, `Evidence`, `list_batch_export_artifacts`, and `list_batch_export_evidence`.

Add:

```python
def serialize_artifact(artifact: Artifact) -> dict[str, object]:
    return {
        "id": artifact.id,
        "artifact_type": artifact.artifact_type,
        "file_name": artifact.file_name,
        "content_type": artifact.content_type,
        "sha256": artifact.sha256,
        "size_bytes": artifact.size_bytes,
        "sensitivity_level": artifact.sensitivity_level,
    }


def serialize_evidence(evidence: Evidence) -> dict[str, object]:
    return {
        "id": evidence.id,
        "evidence_type": evidence.evidence_type,
        "status": evidence.status,
        "summary_json": evidence.summary_json,
        "artifact_id": evidence.artifact_id,
        "manifest_id": evidence.manifest_id,
        "client_safe": evidence.client_safe,
        "sensitivity_level": evidence.sensitivity_level,
    }
```

Add routes:

```python
@router.get("/batches/{batch_id}/artifacts")
def list_rates_batch_artifacts(...):
    ensure batch exists, then return PageResponse(items=[...], total=len(items))


@router.get("/batches/{batch_id}/evidence")
def list_rates_batch_evidence(...):
    ensure batch exists, then return PageResponse(items=[...], total=len(items))
```

- [ ] **Step 5: Run lookup endpoint test**

Run:

```bash
python -m pytest tests/test_rates_csv_export_artifacts.py::test_batch_artifacts_and_evidence_endpoints_return_export_records -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/otm_workbench/modules/rates/exports.py src/otm_workbench/modules/rates/routes.py tests/test_rates_csv_export_artifacts.py
git commit -m "feat: list rates export artifacts"
```

---

## Task 5: Documentation And Full Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README**

Add this sentence to the Rates verification section:

```markdown
The Rates CSV Export Artifacts slice turns validated batches into internal ZIP
artifacts with a client-safe manifest/evidence trail; it does not perform OTM
upload, CSVUTIL packaging, or XML export.
```

- [ ] **Step 2: Run full verification serially**

Run:

```bash
python -m pytest -q
python -m alembic upgrade head
python -m ruff check src tests
```

Expected:

```text
All tests pass
Alembic upgrade succeeds
All checks passed
```

- [ ] **Step 3: Check git status**

Run:

```bash
git status --short --branch
```

Expected: intended tracked changes plus local untracked `OTM_RESOURCES/`.

- [ ] **Step 4: Commit docs**

Run:

```bash
git add README.md
git commit -m "docs: document rates csv export artifacts"
```

Skip if `README.md` was already committed in a prior task.

---

## Self-Review

Spec coverage:

- `POST export-csv`: Tasks 1 through 3.
- ZIP with CSV files and `manifest.json`: Task 2.
- Artifact, manifest, evidence, audit: Task 3.
- Batch status/export timestamp: Task 3.
- Artifacts/evidence lookup endpoints: Task 4.
- Client-safe evidence and manifest without raw row values: Tasks 2 and 3.
- Full verification and docs: Task 5.

No real client names are used. Examples use `OTM1` synthetic values only. This plan intentionally does not add UI, real OTM upload, CSVUTIL, Load Plan integration, XML export, or download endpoint changes.
