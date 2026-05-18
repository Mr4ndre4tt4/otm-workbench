# Load Plan Readiness Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add backend/API support for exporting a persisted Load Plan cutover readiness record as an internal client-safe ZIP artifact.

**Architecture:** Add a `LoadPlanReadinessExport` model and migration, then implement a focused `modules/load_plan/readiness_export.py` service that serializes an existing readiness record into `manifest.json`, `readiness.json`, and `blockers.json`, writes a ZIP under `artifact_root`, and creates Artifact, Manifest, Evidence, AuditLog, and DomainEvent records. Extend the existing Load Plan router with export/list/detail endpoints.

**Tech Stack:** Python, FastAPI, Pydantic, SQLAlchemy ORM, Alembic, pytest, stdlib `json`/`zipfile`/`hashlib`, existing Rates export helpers, existing Load Plan readiness serializer.

---

## File Structure

- Modify `src/otm_workbench/models.py`: add `LoadPlanReadinessExport` after `LoadPlanCutoverReadiness`.
- Create `migrations/versions/d4e9b2c7a6f1_load_plan_readiness_exports.py`: create/drop `load_plan_readiness_exports`.
- Create `src/otm_workbench/modules/load_plan/readiness_export.py`: export service, ZIP generation, serializers, evidence/audit/event creation.
- Modify `src/otm_workbench/modules/load_plan/routes.py`: add export/list/detail endpoints.
- Create `tests/test_load_plan_readiness_export.py`: persistence, export, ZIP content, re-export, routes, and metadata safety tests.
- Modify `README.md`: document backend-only readiness export and include the test file.

No download endpoint, Evidence Hub archive package, real OTM load package, CSVUTIL runtime execution, OTM upload, package status transition, UI, or external Oracle calls are included.

---

### Task 1: Persistence Model And Migration

**Files:**
- Modify: `src/otm_workbench/models.py`
- Create: `migrations/versions/d4e9b2c7a6f1_load_plan_readiness_exports.py`
- Create: `tests/test_load_plan_readiness_export.py`

- [ ] **Step 1: Write the failing table test**

Create `tests/test_load_plan_readiness_export.py`:

```python
import json
from pathlib import Path
import zipfile

from sqlalchemy import inspect

from otm_workbench.database import engine
from otm_workbench.models import (
    Artifact,
    AuditLog,
    DomainEvent,
    Evidence,
    LoadPlanReadinessExport,
)


def create_rate_batch(client, admin_header, scenario_code="ACCESSORIAL_ONLY"):
    response = client.post(
        "/api/v1/modules/rates/batches",
        json={"scenario_code": scenario_code, "name": "Synthetic readiness export batch", "domain_name": "OTM1"},
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


def add_accessorial_table(client, admin_header, batch_id, xid="ACC_COST_001"):
    response = client.post(
        f"/api/v1/modules/rates/batches/{batch_id}/tables",
        json={
            "tables": [
                {
                    "table_name": "ACCESSORIAL_COST",
                    "rows": [
                        {
                            "ACCESSORIAL_COST_GID": f"OTM1.{xid}",
                            "ACCESSORIAL_COST_XID": xid,
                        }
                    ],
                }
            ]
        },
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


def prepare_registered_load_plan_package(client, admin_header):
    batch = create_rate_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])
    preview = client.post(f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview", headers=admin_header)
    assert preview.status_code == 200
    export = client.post(f"/api/v1/modules/rates/batches/{batch['id']}/export-csv", headers=admin_header)
    assert export.status_code == 200
    approval = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/approve",
        json={"approval_note": "Reviewed for synthetic readiness export"},
        headers=admin_header,
    )
    assert approval.status_code == 200
    package = client.post(f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}", headers=admin_header)
    assert package.status_code == 200
    return batch, export.json(), approval.json(), package.json()


def create_cutover_readiness(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    readiness = client.post(
        "/api/v1/modules/load-plan/cutover-readiness/generate",
        json={"package_id": package["id"]},
        headers=admin_header,
    )
    assert readiness.status_code == 200
    return package, readiness.json()["items"][0]


def test_load_plan_readiness_exports_table_exists_after_metadata_reset():
    tables = set(inspect(engine).get_table_names())

    assert "load_plan_readiness_exports" in tables
```

- [ ] **Step 2: Run the failing test**

Run:

```powershell
python -m pytest tests/test_load_plan_readiness_export.py::test_load_plan_readiness_exports_table_exists_after_metadata_reset -q
```

Expected: fail during import because `LoadPlanReadinessExport` does not exist.

- [ ] **Step 3: Add the model**

Append after `LoadPlanCutoverReadiness` in `src/otm_workbench/models.py`:

```python
class LoadPlanReadinessExport(Base, TimestampMixin):
    __tablename__ = "load_plan_readiness_exports"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    package_id: Mapped[str] = mapped_column(ForeignKey("load_plan_packages.id"), index=True)
    readiness_id: Mapped[str] = mapped_column(ForeignKey("load_plan_cutover_readiness.id"), index=True)
    status: Mapped[str] = mapped_column(String, default="EXPORTED", index=True)
    artifact_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    manifest_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    evidence_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    summary_json: Mapped[str] = mapped_column(Text, default="{}")
    exported_by: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    exported_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
```

- [ ] **Step 4: Add the Alembic migration**

Create `migrations/versions/d4e9b2c7a6f1_load_plan_readiness_exports.py`:

```python
"""load plan readiness exports

Revision ID: d4e9b2c7a6f1
Revises: a8d3e5f7b2c1
Create Date: 2026-05-18 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "d4e9b2c7a6f1"
down_revision: str | None = "a8d3e5f7b2c1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "load_plan_readiness_exports",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("environment_id", sa.String(), nullable=True),
        sa.Column("profile_id", sa.String(), nullable=True),
        sa.Column("package_id", sa.String(), nullable=False),
        sa.Column("readiness_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("artifact_id", sa.String(), nullable=True),
        sa.Column("manifest_id", sa.String(), nullable=True),
        sa.Column("evidence_id", sa.String(), nullable=True),
        sa.Column("summary_json", sa.Text(), nullable=False),
        sa.Column("exported_by", sa.String(), nullable=True),
        sa.Column("exported_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["package_id"], ["load_plan_packages.id"]),
        sa.ForeignKeyConstraint(["readiness_id"], ["load_plan_cutover_readiness.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in [
        "project_id",
        "environment_id",
        "profile_id",
        "package_id",
        "readiness_id",
        "status",
        "artifact_id",
        "manifest_id",
        "evidence_id",
        "exported_by",
        "exported_at",
    ]:
        op.create_index(
            f"ix_load_plan_readiness_exports_{column}",
            "load_plan_readiness_exports",
            [column],
        )


def downgrade() -> None:
    for column in [
        "exported_at",
        "exported_by",
        "evidence_id",
        "manifest_id",
        "artifact_id",
        "status",
        "readiness_id",
        "package_id",
        "profile_id",
        "environment_id",
        "project_id",
    ]:
        op.drop_index(f"ix_load_plan_readiness_exports_{column}", table_name="load_plan_readiness_exports")
    op.drop_table("load_plan_readiness_exports")
```

- [ ] **Step 5: Run the table test again**

Run:

```powershell
python -m pytest tests/test_load_plan_readiness_export.py::test_load_plan_readiness_exports_table_exists_after_metadata_reset -q
```

Expected: pass.

- [ ] **Step 6: Commit persistence**

```powershell
git add src/otm_workbench/models.py migrations/versions/d4e9b2c7a6f1_load_plan_readiness_exports.py tests/test_load_plan_readiness_export.py
git commit -m "feat: add load plan readiness export model"
```

---

### Task 2: Export Service And Create Endpoint

**Files:**
- Create: `src/otm_workbench/modules/load_plan/readiness_export.py`
- Modify: `src/otm_workbench/modules/load_plan/routes.py`
- Modify: `tests/test_load_plan_readiness_export.py`

- [ ] **Step 1: Add failing export tests**

Append to `tests/test_load_plan_readiness_export.py`:

```python
def test_readiness_export_rejects_missing_readiness(client, admin_header):
    response = client.post(
        "/api/v1/modules/load-plan/cutover-readiness/missing_readiness/export",
        headers=admin_header,
    )

    assert response.status_code == 404


def test_readiness_export_creates_zip_artifact_manifest_evidence_audit_event(client, admin_header, db_session):
    package, readiness = create_cutover_readiness(client, admin_header, db_session)

    response = client.post(
        f"/api/v1/modules/load-plan/cutover-readiness/{readiness['id']}/export",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["package_id"] == package["id"]
    assert payload["readiness_id"] == readiness["id"]
    assert payload["status"] == "EXPORTED"
    assert payload["summary"]["readiness_status"] == readiness["status"]
    export = db_session.query(LoadPlanReadinessExport).filter(LoadPlanReadinessExport.id == payload["id"]).one()
    artifact = db_session.query(Artifact).filter(Artifact.id == export.artifact_id).one()
    evidence = db_session.query(Evidence).filter(Evidence.id == export.evidence_id).one()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "load_plan.readiness_export.export").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "load_plan.readiness_export.exported").one()
    assert artifact.artifact_type == "load_plan_readiness_export_zip"
    assert artifact.content_type == "application/zip"
    assert artifact.sensitivity_level == "internal"
    assert evidence.evidence_type == "load_plan_readiness_export"
    assert evidence.client_safe is True
    assert audit.target_id == export.id
    assert event.aggregate_id == export.id
```

- [ ] **Step 2: Run the failing tests**

Run:

```powershell
python -m pytest tests/test_load_plan_readiness_export.py::test_readiness_export_rejects_missing_readiness tests/test_load_plan_readiness_export.py::test_readiness_export_creates_zip_artifact_manifest_evidence_audit_event -q
```

Expected: fail because the export route does not exist.

- [ ] **Step 3: Implement export service**

Create `src/otm_workbench/modules/load_plan/readiness_export.py`:

```python
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
    utcnow,
)
from otm_workbench.modules.load_plan.packages import parse_json_list, parse_json_object
from otm_workbench.modules.load_plan.readiness import serialize_cutover_readiness
from otm_workbench.modules.rates.exports import file_sha256, iso_now, utc_timestamp


EXPORTED_STATUS = "EXPORTED"


def json_bytes(payload: object) -> bytes:
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


def generate_readiness_export(
    db: Session,
    *,
    readiness: LoadPlanCutoverReadiness,
    artifact_root: Path,
    exported_by: str,
) -> LoadPlanReadinessExport:
    readiness_payload = serialize_cutover_readiness(readiness)
    blockers = parse_json_list(readiness.blockers_json)
    summary = parse_json_object(readiness.summary_json)
    exported_at_iso = iso_now()
    timestamp = utc_timestamp()
    export_dir = artifact_root / "load_plan" / readiness.package_id / "readiness_exports" / timestamp
    export_dir.mkdir(parents=True, exist_ok=True)
    zip_path = export_dir / f"load_plan_readiness_{readiness.id}.zip"

    readiness_content = json_bytes(readiness_payload)
    blockers_content = json_bytes(blockers)
    entries = [
        entry_metadata("readiness.json", readiness_content),
        entry_metadata("blockers.json", blockers_content),
    ]
    manifest_payload = {
        "schema_version": "load-plan-readiness-export-manifest/v1",
        "manifest_type": "load_plan_readiness_export",
        "source_module": "load_plan",
        "source_entity_type": "load_plan_cutover_readiness",
        "source_entity_id": readiness.id,
        "package_id": readiness.package_id,
        "readiness_status": readiness.status,
        "exported_at": exported_at_iso,
        "exported_by": exported_by,
        "entries": entries,
        "summary": summary,
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

    export_summary = {
        "readiness_status": readiness.status,
        "blocker_count": int(summary.get("blocker_count", len(blockers))),
        "error_count": int(summary.get("error_count", 0)),
        "warning_count": int(summary.get("warning_count", 0)),
        "entry_count": 3,
    }
    export = LoadPlanReadinessExport(
        project_id=readiness.project_id,
        environment_id=readiness.environment_id,
        profile_id=readiness.profile_id,
        package_id=readiness.package_id,
        readiness_id=readiness.id,
        status=EXPORTED_STATUS,
        artifact_id=artifact.id,
        manifest_id=manifest.id,
        summary_json=json.dumps(export_summary, sort_keys=True),
        exported_by=exported_by,
        exported_at=utcnow(),
    )
    db.add(export)
    db.flush()

    evidence_summary = {
        "source_entity_type": "load_plan_readiness_export",
        "source_entity_id": export.id,
        "package_id": readiness.package_id,
        "readiness_id": readiness.id,
        "readiness_status": readiness.status,
        "artifact_id": artifact.id,
        "manifest_id": manifest.id,
        "blocker_count": export_summary["blocker_count"],
        "error_count": export_summary["error_count"],
        "warning_count": export_summary["warning_count"],
    }
    evidence = Evidence(
        project_id=readiness.project_id,
        source_module="load_plan",
        evidence_type="load_plan_readiness_export",
        summary_json=json.dumps(evidence_summary, sort_keys=True),
        artifact_id=artifact.id,
        manifest_id=manifest.id,
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db.add(evidence)
    db.flush()
    export.evidence_id = evidence.id

    db.add(
        AuditLog(
            actor_user_id=exported_by,
            action="load_plan.readiness_export.export",
            target_type="load_plan_readiness_export",
            target_id=export.id,
            metadata_json=json.dumps(
                {
                    "package_id": readiness.package_id,
                    "readiness_id": readiness.id,
                    "readiness_status": readiness.status,
                    "artifact_id": artifact.id,
                    "manifest_id": manifest.id,
                    "evidence_id": evidence.id,
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
                    "package_id": readiness.package_id,
                    "readiness_id": readiness.id,
                    "readiness_status": readiness.status,
                    "status": EXPORTED_STATUS,
                },
                sort_keys=True,
            ),
            status="PENDING",
        )
    )
    db.commit()
    db.refresh(export)
    return export
```

- [ ] **Step 4: Add export route**

Modify `src/otm_workbench/modules/load_plan/routes.py`:

```python
from otm_workbench.models import (
    CsvutilBuild,
    LoadPlanCutoverReadiness,
    LoadPlanPackage,
    LoadPlanReadinessExport,
    LoadPlanReviewItem,
    LoadPlanSequenceSnapshot,
    LoadPlanZipAnalysis,
    RateBatch,
    User,
)
from otm_workbench.modules.load_plan.readiness_export import (
    generate_readiness_export,
    serialize_readiness_export,
)
```

Add this route after `/cutover-readiness/latest` and before `/cutover-readiness/{readiness_id}`:

```python
@router.post("/cutover-readiness/{readiness_id}/export")
def export_cutover_readiness(
    readiness_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    readiness = db.query(LoadPlanCutoverReadiness).filter(LoadPlanCutoverReadiness.id == readiness_id).first()
    if readiness is None:
        raise HTTPException(status_code=404, detail="Load Plan cutover readiness not found.")
    try:
        export = generate_readiness_export(
            db,
            readiness=readiness,
            artifact_root=Path(get_settings().artifact_root),
            exported_by=user.email,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize_readiness_export(export)
```

- [ ] **Step 5: Run focused export tests**

Run:

```powershell
python -m pytest tests/test_load_plan_readiness_export.py::test_readiness_export_rejects_missing_readiness tests/test_load_plan_readiness_export.py::test_readiness_export_creates_zip_artifact_manifest_evidence_audit_event -q
```

Expected: pass.

- [ ] **Step 6: Commit export generation**

```powershell
git add src/otm_workbench/modules/load_plan/readiness_export.py src/otm_workbench/modules/load_plan/routes.py tests/test_load_plan_readiness_export.py
git commit -m "feat: export load plan readiness artifact"
```

---

### Task 3: ZIP Contract, Re-export, And Metadata Safety

**Files:**
- Modify: `tests/test_load_plan_readiness_export.py`
- Modify: `src/otm_workbench/modules/load_plan/readiness_export.py` only if tests expose a defect.

- [ ] **Step 1: Add ZIP content and manifest hash test**

Append:

```python
def test_readiness_export_zip_contains_manifest_readiness_and_blockers(client, admin_header, db_session):
    package, readiness = create_cutover_readiness(client, admin_header, db_session)
    response = client.post(
        f"/api/v1/modules/load-plan/cutover-readiness/{readiness['id']}/export",
        headers=admin_header,
    )
    assert response.status_code == 200
    export = db_session.query(LoadPlanReadinessExport).filter(LoadPlanReadinessExport.id == response.json()["id"]).one()
    artifact = db_session.query(Artifact).filter(Artifact.id == export.artifact_id).one()

    with zipfile.ZipFile(artifact.file_path) as archive:
        assert sorted(archive.namelist()) == ["blockers.json", "manifest.json", "readiness.json"]
        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        readiness_payload = archive.read("readiness.json")
        blockers_payload = archive.read("blockers.json")

    entries = {item["path"]: item for item in manifest["entries"]}
    assert manifest["schema_version"] == "load-plan-readiness-export-manifest/v1"
    assert manifest["manifest_type"] == "load_plan_readiness_export"
    assert manifest["source_entity_id"] == readiness["id"]
    assert entries["readiness.json"]["size_bytes"] == len(readiness_payload)
    assert entries["blockers.json"]["size_bytes"] == len(blockers_payload)
    import hashlib

    assert entries["readiness.json"]["sha256"] == hashlib.sha256(readiness_payload).hexdigest()
    assert entries["blockers.json"]["sha256"] == hashlib.sha256(blockers_payload).hexdigest()
```

- [ ] **Step 2: Add re-export and readiness status preservation tests**

Append:

```python
def test_readiness_export_reexport_creates_new_export_and_artifact(client, admin_header, db_session):
    package, readiness = create_cutover_readiness(client, admin_header, db_session)

    first = client.post(f"/api/v1/modules/load-plan/cutover-readiness/{readiness['id']}/export", headers=admin_header)
    second = client.post(f"/api/v1/modules/load-plan/cutover-readiness/{readiness['id']}/export", headers=admin_header)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] != second.json()["id"]
    assert first.json()["artifact_id"] != second.json()["artifact_id"]
    assert db_session.query(LoadPlanReadinessExport).count() == 2


def test_readiness_export_preserves_readiness_status(client, admin_header, db_session):
    package, readiness = create_cutover_readiness(client, admin_header, db_session)
    response = client.post(
        f"/api/v1/modules/load-plan/cutover-readiness/{readiness['id']}/export",
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["summary"]["readiness_status"] == "MISSING_SEQUENCE"
```

- [ ] **Step 3: Add metadata safety test**

Append:

```python
def test_readiness_export_metadata_does_not_include_raw_values_or_notes(client, admin_header, db_session):
    package, readiness = create_cutover_readiness(client, admin_header, db_session)
    response = client.post(
        f"/api/v1/modules/load-plan/cutover-readiness/{readiness['id']}/export",
        headers=admin_header,
    )

    assert response.status_code == 200
    export = db_session.query(LoadPlanReadinessExport).filter(LoadPlanReadinessExport.id == response.json()["id"]).one()
    evidence = db_session.query(Evidence).filter(Evidence.id == export.evidence_id).one()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "load_plan.readiness_export.export").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "load_plan.readiness_export.exported").one()
    combined = "\n".join([evidence.summary_json, audit.metadata_json, event.payload_json])
    assert "OTM1.ACC_COST_001" not in combined
    assert "DEMO" not in combined
    assert "Synthetic" not in combined
```

- [ ] **Step 4: Run ZIP and safety tests**

Run:

```powershell
python -m pytest tests/test_load_plan_readiness_export.py::test_readiness_export_zip_contains_manifest_readiness_and_blockers tests/test_load_plan_readiness_export.py::test_readiness_export_reexport_creates_new_export_and_artifact tests/test_load_plan_readiness_export.py::test_readiness_export_preserves_readiness_status tests/test_load_plan_readiness_export.py::test_readiness_export_metadata_does_not_include_raw_values_or_notes -q
```

Expected: pass.

- [ ] **Step 5: Commit ZIP contract**

```powershell
git add src/otm_workbench/modules/load_plan/readiness_export.py tests/test_load_plan_readiness_export.py
git commit -m "test: cover load plan readiness export zip"
```

---

### Task 4: Export List/Detail Routes And README

**Files:**
- Modify: `src/otm_workbench/modules/load_plan/routes.py`
- Modify: `tests/test_load_plan_readiness_export.py`
- Modify: `README.md`

- [ ] **Step 1: Add list/detail/filter tests**

Append:

```python
def test_readiness_export_list_detail_and_filters(client, admin_header, db_session):
    package, readiness = create_cutover_readiness(client, admin_header, db_session)
    created = client.post(
        f"/api/v1/modules/load-plan/cutover-readiness/{readiness['id']}/export",
        headers=admin_header,
    ).json()

    listed = client.get("/api/v1/modules/load-plan/cutover-readiness/exports", headers=admin_header)
    filtered = client.get(
        "/api/v1/modules/load-plan/cutover-readiness/exports",
        params={"package_id": package["id"], "readiness_id": readiness["id"], "status": "EXPORTED"},
        headers=admin_header,
    )
    detail = client.get(
        f"/api/v1/modules/load-plan/cutover-readiness/exports/{created['id']}",
        headers=admin_header,
    )

    assert listed.status_code == 200
    assert filtered.status_code == 200
    assert detail.status_code == 200
    assert listed.json()["total"] == 1
    assert filtered.json()["items"][0]["id"] == created["id"]
    assert detail.json()["id"] == created["id"]


def test_readiness_export_detail_rejects_missing_export(client, admin_header):
    response = client.get("/api/v1/modules/load-plan/cutover-readiness/exports/missing_export", headers=admin_header)

    assert response.status_code == 404
```

- [ ] **Step 2: Add list/detail routes**

Modify `src/otm_workbench/modules/load_plan/routes.py`. Place `/cutover-readiness/exports` and `/cutover-readiness/exports/{export_id}` before `/cutover-readiness/{readiness_id}`:

```python
@router.get("/cutover-readiness/exports")
def list_readiness_exports(
    package_id: str | None = None,
    readiness_id: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    query = db.query(LoadPlanReadinessExport)
    if package_id:
        query = query.filter(LoadPlanReadinessExport.package_id == package_id)
    if readiness_id:
        query = query.filter(LoadPlanReadinessExport.readiness_id == readiness_id)
    if status:
        query = query.filter(LoadPlanReadinessExport.status == status)
    exports = query.order_by(LoadPlanReadinessExport.exported_at.desc()).all()
    return PageResponse(items=[serialize_readiness_export(export) for export in exports], total=len(exports))


@router.get("/cutover-readiness/exports/{export_id}")
def get_readiness_export(
    export_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    export = db.query(LoadPlanReadinessExport).filter(LoadPlanReadinessExport.id == export_id).first()
    if export is None:
        raise HTTPException(status_code=404, detail="Load Plan readiness export not found.")
    return serialize_readiness_export(export)
```

- [ ] **Step 3: Run route tests**

Run:

```powershell
python -m pytest tests/test_load_plan_readiness_export.py::test_readiness_export_list_detail_and_filters tests/test_load_plan_readiness_export.py::test_readiness_export_detail_rejects_missing_export -q
```

Expected: pass.

- [ ] **Step 4: Update README**

Add after the Load Plan Cutover Readiness paragraph:

```markdown
The Load Plan Readiness Export slice exports persisted cutover readiness records
as internal ZIP artifacts with `manifest.json`, `readiness.json`, and
`blockers.json`, plus client-safe evidence, audit, and event records. It does
not provide a download endpoint, execute CSVUTIL, connect to OTM, or transition
package status.
```

Extend the verification command:

```powershell
python -m pytest tests/test_reference_catalog.py tests/test_rates_dictionary.py tests/test_rates_csv_preview.py tests/test_rates_batch_approval.py tests/test_load_plan_package_intake.py tests/test_load_plan_csvutil_builder.py tests/test_load_plan_zip_analysis.py tests/test_load_plan_review_queue.py tests/test_load_plan_review_decisions.py tests/test_load_plan_sequence_blockers.py tests/test_load_plan_cutover_readiness.py tests/test_load_plan_readiness_export.py
```

- [ ] **Step 5: Run focused export tests**

Run:

```powershell
python -m pytest tests/test_load_plan_readiness_export.py -q
```

Expected: all readiness export tests pass.

- [ ] **Step 6: Commit routes and README**

```powershell
git add src/otm_workbench/modules/load_plan/routes.py README.md tests/test_load_plan_readiness_export.py
git commit -m "feat: expose load plan readiness exports"
```

---

### Task 5: Full Verification, PR, And Merge

**Files:**
- No new code files unless verification exposes a defect.

- [ ] **Step 1: Run full verification**

Run:

```powershell
python -m pytest -q
python -m alembic upgrade head
python -m ruff check src tests
```

Expected:

- All tests pass.
- Alembic upgrades through `d4e9b2c7a6f1`.
- Ruff reports `All checks passed!`.

- [ ] **Step 2: Inspect git status**

Run:

```powershell
git status --short --branch
```

Expected:

```text
## codex/load-plan-readiness-export
?? OTM_RESOURCES/
```

`OTM_RESOURCES/` must remain untracked.

- [ ] **Step 3: Push branch**

```powershell
git push -u origin codex/load-plan-readiness-export
```

- [ ] **Step 4: Open PR**

Use GitHub connector.

Title:

```text
Load Plan Readiness Export
```

Body:

```markdown
## Summary
- Add Load Plan readiness export persistence and migration.
- Export persisted cutover readiness as internal ZIP artifacts with manifest, readiness, and blockers payloads.
- Add export/list/detail APIs with client-safe evidence, audit, and domain events.

## Test plan
- `python -m pytest -q`
- `python -m alembic upgrade head`
- `python -m ruff check src tests`
```

- [ ] **Step 5: Merge PR and sync main**

After PR creation, merge with expected head SHA, then:

```powershell
git checkout main
git pull --ff-only origin main
git branch -d codex/load-plan-readiness-export
git status --short --branch
```

Expected: `main` is current and only `OTM_RESOURCES/` is untracked.

---

## Self-Review Checklist

- Spec coverage: persistence, export ZIP, artifact/manifest/evidence/audit/event, list/detail routes, re-export, safety tests, README, and exclusions are covered.
- Placeholder scan: no deferred implementation text is present; all steps include concrete files, snippets, and commands.
- Type consistency: model `LoadPlanReadinessExport`, table `load_plan_readiness_exports`, route prefix `/cutover-readiness`, artifact/evidence/action/event names, and status `EXPORTED` match the design spec.
- Data safety: examples use synthetic `OTM1`/`DEMO`; evidence/audit/events avoid raw row values and decision notes.
