# Load Plan CSVUTIL Builder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add backend/API support for generating internal CSVUTIL CTL/CL control artifacts from registered Load Plan packages.

**Architecture:** Add a `CsvutilBuild` model and migration, then implement a focused `modules/load_plan/csvutil.py` service that validates a registered package, writes deterministic CTL/CL files, records artifact/manifest/evidence/audit/event metadata, and returns a serializable build contract. Extend the existing Load Plan router with build/list/detail endpoints.

**Tech Stack:** Python, FastAPI, SQLAlchemy, Alembic, SQLite, pytest, Ruff.

---

## File Structure

- Modify `src/otm_workbench/models.py`: add `CsvutilBuild`.
- Create `migrations/versions/e8a1c5d9f0b2_load_plan_csvutil_builder.py`: create/drop `csvutil_builds`.
- Create `src/otm_workbench/modules/load_plan/csvutil.py`: build service, serializers, deterministic CTL/CL generation.
- Modify `src/otm_workbench/modules/load_plan/routes.py`: add CSVUTIL build/list/detail endpoints.
- Create `tests/test_load_plan_csvutil_builder.py`: model, API, artifacts, manifest, evidence, audit, event, rebuild tests.
- Modify `README.md`: mention CSVUTIL builder verification.

No OTM connection, CSVUTIL runtime execution, ZIP analysis, setup review, cutover readiness, or UI is included.

Before implementing, confirm table assumptions against `OTM_RESOURCES/DATA_DICT26B/data_dictionary/json/data_dict`. Test data must use synthetic `OTM1` values only.

---

## Task 1: Model And Migration

**Files:**
- Modify: `src/otm_workbench/models.py`
- Create: `migrations/versions/e8a1c5d9f0b2_load_plan_csvutil_builder.py`
- Test: `tests/test_load_plan_csvutil_builder.py`

- [ ] **Step 1: Write failing model/migration test**

Create `tests/test_load_plan_csvutil_builder.py`:

```python
import json
from pathlib import Path

from sqlalchemy import inspect

from otm_workbench.database import engine
from otm_workbench.models import Artifact, AuditLog, CsvutilBuild, DomainEvent, Evidence, LoadPlanPackage, Manifest


def create_rate_batch(client, admin_header, scenario_code="ACCESSORIAL_ONLY"):
    response = client.post(
        "/api/v1/modules/rates/batches",
        json={"scenario_code": scenario_code, "name": "Synthetic CSVUTIL batch", "domain_name": "OTM1"},
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
        json={"approval_note": "Reviewed for synthetic CSVUTIL package"},
        headers=admin_header,
    )
    assert approval.status_code == 200
    package = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    )
    assert package.status_code == 200
    return batch, export.json(), approval.json(), package.json()


def test_csvutil_builds_table_exists_after_metadata_reset():
    tables = set(inspect(engine).get_table_names())

    assert "csvutil_builds" in tables
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
python -m pytest tests/test_load_plan_csvutil_builder.py::test_csvutil_builds_table_exists_after_metadata_reset -q
```

Expected: FAIL because `CsvutilBuild` does not exist.

- [ ] **Step 3: Add `CsvutilBuild` model**

In `src/otm_workbench/models.py`, after `LoadPlanPackage`, add:

```python
class CsvutilBuild(Base, TimestampMixin):
    __tablename__ = "csvutil_builds"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    package_id: Mapped[str] = mapped_column(ForeignKey("load_plan_packages.id"), index=True)
    status: Mapped[str] = mapped_column(String, default="BUILT", index=True)
    ctl_artifact_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    cl_artifact_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    manifest_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    evidence_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    summary_json: Mapped[str] = mapped_column(Text, default="{}")
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)
    built_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
```

- [ ] **Step 4: Add migration**

Create `migrations/versions/e8a1c5d9f0b2_load_plan_csvutil_builder.py`:

```python
"""load plan csvutil builder

Revision ID: e8a1c5d9f0b2
Revises: d2f7b9c4a8e3
Create Date: 2026-05-18 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e8a1c5d9f0b2"
down_revision: Union[str, None] = "d2f7b9c4a8e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "csvutil_builds",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("environment_id", sa.String(), nullable=True),
        sa.Column("profile_id", sa.String(), nullable=True),
        sa.Column("package_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("ctl_artifact_id", sa.String(), nullable=True),
        sa.Column("cl_artifact_id", sa.String(), nullable=True),
        sa.Column("manifest_id", sa.String(), nullable=True),
        sa.Column("evidence_id", sa.String(), nullable=True),
        sa.Column("summary_json", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("built_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["package_id"], ["load_plan_packages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_csvutil_builds_project_id"), "csvutil_builds", ["project_id"])
    op.create_index(op.f("ix_csvutil_builds_environment_id"), "csvutil_builds", ["environment_id"])
    op.create_index(op.f("ix_csvutil_builds_profile_id"), "csvutil_builds", ["profile_id"])
    op.create_index(op.f("ix_csvutil_builds_package_id"), "csvutil_builds", ["package_id"])
    op.create_index(op.f("ix_csvutil_builds_status"), "csvutil_builds", ["status"])
    op.create_index(op.f("ix_csvutil_builds_ctl_artifact_id"), "csvutil_builds", ["ctl_artifact_id"])
    op.create_index(op.f("ix_csvutil_builds_cl_artifact_id"), "csvutil_builds", ["cl_artifact_id"])
    op.create_index(op.f("ix_csvutil_builds_manifest_id"), "csvutil_builds", ["manifest_id"])
    op.create_index(op.f("ix_csvutil_builds_evidence_id"), "csvutil_builds", ["evidence_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_csvutil_builds_evidence_id"), table_name="csvutil_builds")
    op.drop_index(op.f("ix_csvutil_builds_manifest_id"), table_name="csvutil_builds")
    op.drop_index(op.f("ix_csvutil_builds_cl_artifact_id"), table_name="csvutil_builds")
    op.drop_index(op.f("ix_csvutil_builds_ctl_artifact_id"), table_name="csvutil_builds")
    op.drop_index(op.f("ix_csvutil_builds_status"), table_name="csvutil_builds")
    op.drop_index(op.f("ix_csvutil_builds_package_id"), table_name="csvutil_builds")
    op.drop_index(op.f("ix_csvutil_builds_profile_id"), table_name="csvutil_builds")
    op.drop_index(op.f("ix_csvutil_builds_environment_id"), table_name="csvutil_builds")
    op.drop_index(op.f("ix_csvutil_builds_project_id"), table_name="csvutil_builds")
    op.drop_table("csvutil_builds")
```

- [ ] **Step 5: Run model test**

Run:

```bash
python -m pytest tests/test_load_plan_csvutil_builder.py::test_csvutil_builds_table_exists_after_metadata_reset -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add src/otm_workbench/models.py migrations/versions/e8a1c5d9f0b2_load_plan_csvutil_builder.py tests/test_load_plan_csvutil_builder.py
git commit -m "feat: add csvutil build model"
```

---

## Task 2: CSVUTIL Build Service And Endpoint

**Files:**
- Create: `src/otm_workbench/modules/load_plan/csvutil.py`
- Modify: `src/otm_workbench/modules/load_plan/routes.py`
- Test: `tests/test_load_plan_csvutil_builder.py`

- [ ] **Step 1: Add failing build tests**

Append to `tests/test_load_plan_csvutil_builder.py`:

```python
def test_csvutil_build_rejects_missing_package(client, admin_header):
    response = client.post(
        "/api/v1/modules/load-plan/csvutil/build",
        json={"package_id": "missing_package"},
        headers=admin_header,
    )

    assert response.status_code == 404


def test_csvutil_build_succeeds_for_registered_package(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)

    response = client.post(
        "/api/v1/modules/load-plan/csvutil/build",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    build = db_session.query(CsvutilBuild).filter(CsvutilBuild.id == payload["id"]).one()
    assert payload["package_id"] == package["id"]
    assert payload["status"] == "BUILT"
    assert payload["ctl_artifact_id"]
    assert payload["cl_artifact_id"]
    assert payload["manifest_id"]
    assert payload["evidence_id"]
    assert payload["summary"]["table_count"] == 1
    assert payload["summary"]["row_count"] == 1
    assert payload["summary"]["package_type"] == "rates_csv_zip"
    assert build.created_by == "admin@example.com"
    assert build.built_at is not None
```

- [ ] **Step 2: Run build tests to verify failure**

Run:

```bash
python -m pytest tests/test_load_plan_csvutil_builder.py::test_csvutil_build_rejects_missing_package tests/test_load_plan_csvutil_builder.py::test_csvutil_build_succeeds_for_registered_package -q
```

Expected: FAIL because build service/routes do not exist.

- [ ] **Step 3: Implement CSVUTIL service**

Create `src/otm_workbench/modules/load_plan/csvutil.py`:

```python
from dataclasses import dataclass
import json
from pathlib import Path

from sqlalchemy.orm import Session

from otm_workbench.models import Artifact, AuditLog, CsvutilBuild, DomainEvent, Evidence, LoadPlanPackage, Manifest, utcnow
from otm_workbench.modules.load_plan.packages import parse_json_list, parse_json_object
from otm_workbench.modules.rates.exports import file_sha256, iso_now, utc_timestamp


@dataclass(frozen=True)
class CsvutilBuildResult:
    id: str
    package_id: str
    status: str
    ctl_artifact_id: str
    cl_artifact_id: str
    manifest_id: str
    evidence_id: str
    summary: dict[str, object]


def csv_relative_name(index: int, table_name: str) -> str:
    return f"csv/{index:03d}_{table_name}.csv"


def build_ctl_text(package: LoadPlanPackage, load_sequence: list[dict[str, object]]) -> str:
    lines = [
        "# OTM Workbench CSVUTIL CTL",
        f"# package_id={package.id}",
        f"# source_module={package.source_module}",
    ]
    for index, item in enumerate(load_sequence, start=1):
        table_name = str(item["table_name"])
        lines.append(f"{index:03d},{table_name},{csv_relative_name(index, table_name)}")
    return "\n".join(lines) + "\n"


def build_cl_text(package: LoadPlanPackage, load_sequence: list[dict[str, object]]) -> str:
    lines = [
        "# OTM Workbench CSVUTIL CL",
        f"# package_id={package.id}",
    ]
    for index, item in enumerate(load_sequence, start=1):
        table_name = str(item["table_name"])
        lines.append(f"LOAD {table_name} FROM {csv_relative_name(index, table_name)}")
    return "\n".join(lines) + "\n"


def serialize_csvutil_build(build: CsvutilBuild) -> dict[str, object]:
    return {
        "id": build.id,
        "project_id": build.project_id,
        "environment_id": build.environment_id,
        "profile_id": build.profile_id,
        "package_id": build.package_id,
        "status": build.status,
        "ctl_artifact_id": build.ctl_artifact_id,
        "cl_artifact_id": build.cl_artifact_id,
        "manifest_id": build.manifest_id,
        "evidence_id": build.evidence_id,
        "summary": parse_json_object(build.summary_json),
        "created_by": build.created_by,
        "built_at": build.built_at.isoformat() if build.built_at else None,
    }


def ensure_buildable_package(package: LoadPlanPackage) -> list[dict[str, object]]:
    if package.status != "REGISTERED":
        raise ValueError("Load Plan package must be REGISTERED before CSVUTIL build.")
    if not package.artifact_id or not package.manifest_id:
        raise ValueError("Load Plan package must reference source artifact and manifest before CSVUTIL build.")
    load_sequence = parse_json_list(package.load_sequence_json)
    if not load_sequence:
        raise ValueError("Load Plan package must have a load sequence before CSVUTIL build.")
    row_count = sum(int(item.get("row_count", 0)) for item in load_sequence)
    if row_count == 0:
        raise ValueError("Load Plan package must have rows before CSVUTIL build.")
    return load_sequence


def create_artifact(
    db: Session,
    *,
    package: LoadPlanPackage,
    artifact_type: str,
    path: Path,
) -> Artifact:
    digest, size = file_sha256(path)
    artifact = Artifact(
        project_id=package.project_id,
        source_module="load_plan",
        artifact_type=artifact_type,
        file_path=str(path),
        file_name=path.name,
        content_type="text/plain",
        sha256=digest,
        size_bytes=size,
        sensitivity_level="internal",
    )
    db.add(artifact)
    db.flush()
    return artifact


def generate_csvutil_build(
    db: Session,
    *,
    package: LoadPlanPackage,
    artifact_root: Path,
    built_by: str,
) -> CsvutilBuild:
    load_sequence = ensure_buildable_package(package)
    timestamp = utc_timestamp()
    build_dir = artifact_root / "load_plan" / package.id / "csvutil" / timestamp
    build_dir.mkdir(parents=True, exist_ok=True)
    ctl_path = build_dir / f"csvutil_{package.id}.ctl"
    cl_path = build_dir / f"csvutil_{package.id}.cl"
    ctl_path.write_text(build_ctl_text(package, load_sequence), encoding="utf-8")
    cl_path.write_text(build_cl_text(package, load_sequence), encoding="utf-8")

    ctl_artifact = create_artifact(db, package=package, artifact_type="csvutil_ctl", path=ctl_path)
    cl_artifact = create_artifact(db, package=package, artifact_type="csvutil_cl", path=cl_path)
    package_summary = parse_json_object(package.summary_json)
    built_at = iso_now()
    files = [
        {
            "artifact_type": ctl_artifact.artifact_type,
            "file_name": ctl_artifact.file_name,
            "sha256": ctl_artifact.sha256,
            "size_bytes": ctl_artifact.size_bytes,
        },
        {
            "artifact_type": cl_artifact.artifact_type,
            "file_name": cl_artifact.file_name,
            "sha256": cl_artifact.sha256,
            "size_bytes": cl_artifact.size_bytes,
        },
    ]
    manifest_payload = {
        "schema_version": "load-plan-csvutil-build-manifest/v1",
        "manifest_type": "csvutil_build",
        "source_module": "load_plan",
        "source_entity_type": "load_plan_package",
        "source_entity_id": package.id,
        "package": {
            "id": package.id,
            "source_module": package.source_module,
            "source_entity_id": package.source_entity_id,
            "package_type": package.package_type,
        },
        "files": files,
        "load_sequence": load_sequence,
        "built_at": built_at,
        "built_by": built_by,
    }
    manifest = Manifest(
        project_id=package.project_id,
        source_module="load_plan",
        status="CREATED",
        manifest_json=json.dumps(manifest_payload, indent=2, sort_keys=True),
    )
    db.add(manifest)
    db.flush()

    summary = {
        "package_id": package.id,
        "source_module": package.source_module,
        "source_entity_type": package.source_entity_type,
        "source_entity_id": package.source_entity_id,
        "package_type": package.package_type,
        "table_count": len(load_sequence),
        "row_count": sum(int(item.get("row_count", 0)) for item in load_sequence),
        "ctl_artifact_type": "csvutil_ctl",
        "cl_artifact_type": "csvutil_cl",
    }
    build = CsvutilBuild(
        project_id=package.project_id,
        environment_id=package.environment_id,
        profile_id=package.profile_id,
        package_id=package.id,
        status="BUILT",
        ctl_artifact_id=ctl_artifact.id,
        cl_artifact_id=cl_artifact.id,
        manifest_id=manifest.id,
        summary_json=json.dumps(summary, sort_keys=True),
        created_by=built_by,
        built_at=utcnow(),
    )
    db.add(build)
    db.flush()

    evidence_summary = {
        "source_entity_type": "csvutil_build",
        "source_entity_id": build.id,
        "package_id": package.id,
        "source_package_type": package.package_type,
        "table_count": summary["table_count"],
        "row_count": summary["row_count"],
        "ctl_artifact_id": ctl_artifact.id,
        "cl_artifact_id": cl_artifact.id,
        "manifest_id": manifest.id,
        "status": "BUILT",
    }
    evidence = Evidence(
        project_id=package.project_id,
        source_module="load_plan",
        evidence_type="csvutil_build",
        summary_json=json.dumps(evidence_summary, sort_keys=True),
        artifact_id=ctl_artifact.id,
        manifest_id=manifest.id,
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db.add(evidence)
    db.flush()

    build.evidence_id = evidence.id
    db.add(
        AuditLog(
            actor_user_id=built_by,
            action="load_plan.csvutil.build",
            target_type="csvutil_build",
            target_id=build.id,
            metadata_json=json.dumps(
                {
                    "package_id": package.id,
                    "ctl_artifact_id": ctl_artifact.id,
                    "cl_artifact_id": cl_artifact.id,
                    "manifest_id": manifest.id,
                    "evidence_id": evidence.id,
                },
                sort_keys=True,
            ),
        )
    )
    db.add(
        DomainEvent(
            event_type="load_plan.csvutil.built",
            source_module="load_plan",
            project_id=package.project_id,
            aggregate_type="csvutil_build",
            aggregate_id=build.id,
            payload_json=json.dumps({"package_id": package.id, "status": "BUILT"}, sort_keys=True),
            status="PENDING",
        )
    )
    db.commit()
    db.refresh(build)
    return build
```

- [ ] **Step 4: Add API route**

Modify `src/otm_workbench/modules/load_plan/routes.py`.

Add imports:

```python
from pydantic import BaseModel
from pathlib import Path

from otm_workbench.config import get_settings
from otm_workbench.models import CsvutilBuild
from otm_workbench.modules.load_plan.csvutil import generate_csvutil_build, serialize_csvutil_build
```

Add request model:

```python
class CsvutilBuildRequest(BaseModel):
    package_id: str
```

Add route:

```python
@router.post("/csvutil/build")
def build_csvutil_artifacts(
    payload: CsvutilBuildRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    package = db.query(LoadPlanPackage).filter(LoadPlanPackage.id == payload.package_id).first()
    if package is None:
        raise HTTPException(status_code=404, detail="Load Plan package not found.")
    try:
        build = generate_csvutil_build(
            db,
            package=package,
            artifact_root=Path(get_settings().artifact_root),
            built_by=user.email,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize_csvutil_build(build)
```

- [ ] **Step 5: Run build tests**

Run:

```bash
python -m pytest tests/test_load_plan_csvutil_builder.py::test_csvutil_build_rejects_missing_package tests/test_load_plan_csvutil_builder.py::test_csvutil_build_succeeds_for_registered_package -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add src/otm_workbench/modules/load_plan/csvutil.py src/otm_workbench/modules/load_plan/routes.py tests/test_load_plan_csvutil_builder.py
git commit -m "feat: build csvutil artifacts"
```

---

## Task 3: Artifact, Manifest, Evidence, Audit, Event

**Files:**
- Modify: `src/otm_workbench/modules/load_plan/csvutil.py`
- Test: `tests/test_load_plan_csvutil_builder.py`

- [ ] **Step 1: Add artifact and metadata tests**

Append to `tests/test_load_plan_csvutil_builder.py`:

```python
def test_csvutil_build_creates_ctl_cl_manifest_evidence_audit_and_event(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)

    response = client.post(
        "/api/v1/modules/load-plan/csvutil/build",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    ctl = db_session.query(Artifact).filter(Artifact.id == payload["ctl_artifact_id"]).one()
    cl = db_session.query(Artifact).filter(Artifact.id == payload["cl_artifact_id"]).one()
    manifest = db_session.query(Manifest).filter(Manifest.id == payload["manifest_id"]).one()
    evidence = db_session.query(Evidence).filter(Evidence.id == payload["evidence_id"]).one()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "load_plan.csvutil.build").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "load_plan.csvutil.built").one()

    ctl_text = Path(ctl.file_path).read_text(encoding="utf-8")
    cl_text = Path(cl.file_path).read_text(encoding="utf-8")
    manifest_json = json.loads(manifest.manifest_json)

    assert ctl.artifact_type == "csvutil_ctl"
    assert cl.artifact_type == "csvutil_cl"
    assert ctl.content_type == "text/plain"
    assert cl.content_type == "text/plain"
    assert "001,ACCESSORIAL_COST,csv/001_ACCESSORIAL_COST.csv" in ctl_text
    assert "LOAD ACCESSORIAL_COST FROM csv/001_ACCESSORIAL_COST.csv" in cl_text
    assert "OTM1.ACC_COST_001" not in ctl_text
    assert "OTM1.ACC_COST_001" not in cl_text
    assert manifest_json["manifest_type"] == "csvutil_build"
    assert manifest_json["package"]["id"] == package["id"]
    assert {item["artifact_type"] for item in manifest_json["files"]} == {"csvutil_ctl", "csvutil_cl"}
    assert evidence.client_safe is True
    assert evidence.evidence_type == "csvutil_build"
    assert evidence.artifact_id == ctl.id
    assert "OTM1.ACC_COST_001" not in evidence.summary_json
    assert audit.target_id == payload["id"]
    assert event.aggregate_id == payload["id"]
    assert event.status == "PENDING"
```

- [ ] **Step 2: Run artifact metadata test**

Run:

```bash
python -m pytest tests/test_load_plan_csvutil_builder.py::test_csvutil_build_creates_ctl_cl_manifest_evidence_audit_and_event -q
```

Expected: PASS if Task 2 implemented all metadata; otherwise FAIL and fix the missing fields.

- [ ] **Step 3: Commit**

Run:

```bash
git add src/otm_workbench/modules/load_plan/csvutil.py tests/test_load_plan_csvutil_builder.py
git commit -m "feat: record csvutil build metadata"
```

Skip the commit if no code changed after the test.

---

## Task 4: List, Detail, Preconditions, Rebuild History

**Files:**
- Modify: `src/otm_workbench/modules/load_plan/routes.py`
- Test: `tests/test_load_plan_csvutil_builder.py`

- [ ] **Step 1: Add list/detail/precondition/rebuild tests**

Append to `tests/test_load_plan_csvutil_builder.py`:

```python
def test_csvutil_build_list_and_detail(client, admin_header):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    created = client.post(
        "/api/v1/modules/load-plan/csvutil/build",
        json={"package_id": package["id"]},
        headers=admin_header,
    ).json()

    listed = client.get("/api/v1/modules/load-plan/csvutil/builds", headers=admin_header)
    detail = client.get(f"/api/v1/modules/load-plan/csvutil/builds/{created['id']}", headers=admin_header)

    assert listed.status_code == 200
    assert detail.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == created["id"]
    assert detail.json()["summary"]["package_type"] == "rates_csv_zip"


def test_csvutil_build_rejects_package_without_artifact_or_manifest(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    package_row = db_session.query(LoadPlanPackage).filter(LoadPlanPackage.id == package["id"]).one()
    package_row.artifact_id = None
    package_row.manifest_id = None
    db_session.commit()

    response = client.post(
        "/api/v1/modules/load-plan/csvutil/build",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "artifact" in response.json()["message"].lower()


def test_csvutil_build_rejects_empty_load_sequence(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    package_row = db_session.query(LoadPlanPackage).filter(LoadPlanPackage.id == package["id"]).one()
    package_row.load_sequence_json = "[]"
    db_session.commit()

    response = client.post(
        "/api/v1/modules/load-plan/csvutil/build",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "load sequence" in response.json()["message"].lower()


def test_csvutil_rebuild_creates_separate_build_history(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)

    first = client.post(
        "/api/v1/modules/load-plan/csvutil/build",
        json={"package_id": package["id"]},
        headers=admin_header,
    )
    second = client.post(
        "/api/v1/modules/load-plan/csvutil/build",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] != second.json()["id"]
    assert db_session.query(CsvutilBuild).count() == 2
    assert db_session.query(Evidence).filter(Evidence.evidence_type == "csvutil_build").count() == 2
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/test_load_plan_csvutil_builder.py::test_csvutil_build_list_and_detail tests/test_load_plan_csvutil_builder.py::test_csvutil_build_rejects_package_without_artifact_or_manifest tests/test_load_plan_csvutil_builder.py::test_csvutil_build_rejects_empty_load_sequence tests/test_load_plan_csvutil_builder.py::test_csvutil_rebuild_creates_separate_build_history -q
```

Expected: FAIL if list/detail routes are missing; preconditions and rebuild may already pass.

- [ ] **Step 3: Add list/detail routes**

Modify `src/otm_workbench/modules/load_plan/routes.py` and add:

```python
@router.get("/csvutil/builds")
def list_csvutil_builds(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    builds = db.query(CsvutilBuild).order_by(CsvutilBuild.created_at.desc()).all()
    items = [serialize_csvutil_build(build) for build in builds]
    return PageResponse(items=items, total=len(items))


@router.get("/csvutil/builds/{build_id}")
def get_csvutil_build(
    build_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    build = db.query(CsvutilBuild).filter(CsvutilBuild.id == build_id).first()
    if build is None:
        raise HTTPException(status_code=404, detail="CSVUTIL build not found.")
    return serialize_csvutil_build(build)
```

- [ ] **Step 4: Run list/detail/precondition/rebuild tests**

Run:

```bash
python -m pytest tests/test_load_plan_csvutil_builder.py::test_csvutil_build_list_and_detail tests/test_load_plan_csvutil_builder.py::test_csvutil_build_rejects_package_without_artifact_or_manifest tests/test_load_plan_csvutil_builder.py::test_csvutil_build_rejects_empty_load_sequence tests/test_load_plan_csvutil_builder.py::test_csvutil_rebuild_creates_separate_build_history -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/otm_workbench/modules/load_plan/routes.py tests/test_load_plan_csvutil_builder.py
git commit -m "feat: expose csvutil build history"
```

---

## Task 5: Documentation And Full Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README**

Add after the Load Plan Package Intake paragraph:

```markdown
The Load Plan CSVUTIL Builder slice generates internal CTL/CL control artifacts
from registered Load Plan packages, with manifest/evidence metadata, without
executing CSVUTIL, connecting to OTM, or producing cutover readiness.
```

Update the verification command:

```powershell
python -m pytest tests/test_reference_catalog.py tests/test_rates_dictionary.py tests/test_rates_csv_preview.py tests/test_rates_batch_approval.py tests/test_load_plan_package_intake.py tests/test_load_plan_csvutil_builder.py
```

- [ ] **Step 2: Run full verification**

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

- [ ] **Step 3: Scan package examples for synthetic naming**

Run:

```bash
rg -n "Synthetic|OTM1|PUBLIC|DEMO" README.md src tests docs/superpowers/specs/2026-05-18-load-plan-csvutil-builder-design.md docs/superpowers/plans/2026-05-18-load-plan-csvutil-builder.md
```

Expected: examples use synthetic identifiers such as `Synthetic` and `OTM1`.

- [ ] **Step 4: Check git status**

Run:

```bash
git status --short --branch
```

Expected: intended tracked changes plus local untracked `OTM_RESOURCES/`.

- [ ] **Step 5: Commit docs**

Run:

```bash
git add README.md
git commit -m "docs: document load plan csvutil builder"
```

Skip if README was already committed in a prior task.

---

## Self-Review

Spec coverage:

- `CsvutilBuild` model and migration: Task 1.
- Build endpoint and preconditions: Task 2 and Task 4.
- CTL/CL artifact generation: Task 2 and Task 3.
- Manifest/evidence/audit/event: Task 3.
- List/detail endpoints: Task 4.
- Rebuild creates separate history: Task 4.
- README and full verification: Task 5.

Scope guardrails:

- No CSVUTIL runtime execution.
- No OTM connection.
- No claim of OTM acceptance.
- No ZIP analysis.
- No setup review queue.
- No cutover readiness.
- No UI.

The plan uses synthetic `OTM1` data only and does not copy raw row values into CTL, CL, manifest, or evidence summaries.
