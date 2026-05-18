# Load Plan Cutover Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add backend/API support for generating persisted cutover readiness assessments from latest Load Plan sequence snapshots.

**Architecture:** Add a `LoadPlanCutoverReadiness` model and migration, then implement a focused `modules/load_plan/readiness.py` service that consumes the latest `LoadPlanSequenceSnapshot` rather than recalculating blockers. Extend the Load Plan router with generate/list/detail/latest endpoints and preserve client-safe evidence, audit, and event records.

**Tech Stack:** Python, FastAPI, Pydantic, SQLAlchemy ORM, Alembic, pytest, stdlib `json`, existing Load Plan package and sequence snapshot APIs.

---

## File Structure

- Modify `src/otm_workbench/models.py`: add `LoadPlanCutoverReadiness` after `LoadPlanSequenceSnapshot`.
- Create `migrations/versions/a8d3e5f7b2c1_load_plan_cutover_readiness.py`: create/drop `load_plan_cutover_readiness`.
- Create `src/otm_workbench/modules/load_plan/readiness.py`: readiness derivation, aggregation, serializers, evidence/audit/event creation.
- Modify `src/otm_workbench/modules/load_plan/routes.py`: add request model and cutover readiness routes.
- Create `tests/test_load_plan_cutover_readiness.py`: persistence, generation, statuses, evidence/audit/event, route tests.
- Modify `README.md`: document the backend-only readiness slice and include the test file.

No export/download, cutover execution, CSVUTIL runtime execution, OTM upload, package status transitions, UI, or external Oracle calls are included.

---

### Task 1: Persistence Model And Migration

**Files:**
- Modify: `src/otm_workbench/models.py`
- Create: `migrations/versions/a8d3e5f7b2c1_load_plan_cutover_readiness.py`
- Create: `tests/test_load_plan_cutover_readiness.py`

- [ ] **Step 1: Write the failing table test**

Create `tests/test_load_plan_cutover_readiness.py`:

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
    LoadPlanCutoverReadiness,
    LoadPlanPackage,
    LoadPlanSequenceSnapshot,
)


def create_rate_batch(client, admin_header, scenario_code="ACCESSORIAL_ONLY"):
    response = client.post(
        "/api/v1/modules/rates/batches",
        json={"scenario_code": scenario_code, "name": "Synthetic readiness batch", "domain_name": "OTM1"},
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
        json={"approval_note": "Reviewed for synthetic cutover readiness"},
        headers=admin_header,
    )
    assert approval.status_code == 200
    package = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    )
    assert package.status_code == 200
    return batch, export.json(), approval.json(), package.json()


def rewrite_export_with_unknown_column(db_session, export):
    artifact = db_session.query(Artifact).filter(Artifact.id == export["artifact_id"]).one()
    artifact_path = Path(artifact.file_path)
    rewritten_path = artifact_path.with_suffix(".cutover-readiness.zip")
    with zipfile.ZipFile(artifact_path) as original:
        entries = {
            name: original.read(name)
            for name in original.namelist()
            if name != "csv/001_ACCESSORIAL_COST.csv"
        }
    entries["csv/001_ACCESSORIAL_COST.csv"] = (
        "ACCESSORIAL_COST\n"
        "ACCESSORIAL_COST_GID,ACCESSORIAL_COST_XID,SYNTHETIC_UNKNOWN_COLUMN\n"
        "OTM1.ACC_COST_001,ACC_COST_001,DEMO\n"
    ).encode("utf-8")
    with zipfile.ZipFile(rewritten_path, "w", compression=zipfile.ZIP_DEFLATED) as rewritten:
        for name, content in entries.items():
            rewritten.writestr(name, content)
    artifact.file_path = str(rewritten_path)
    artifact.file_name = rewritten_path.name
    artifact.size_bytes = rewritten_path.stat().st_size
    db_session.commit()


def create_sequence_snapshot(client, admin_header, package):
    response = client.post(
        "/api/v1/modules/load-plan/sequence/snapshots",
        json={"package_id": package["id"]},
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()


def test_load_plan_cutover_readiness_table_exists_after_metadata_reset():
    tables = set(inspect(engine).get_table_names())

    assert "load_plan_cutover_readiness" in tables
```

- [ ] **Step 2: Run the failing test**

Run:

```powershell
python -m pytest tests/test_load_plan_cutover_readiness.py::test_load_plan_cutover_readiness_table_exists_after_metadata_reset -q
```

Expected: fail during import because `LoadPlanCutoverReadiness` does not exist.

- [ ] **Step 3: Add the model**

Append after `LoadPlanSequenceSnapshot` in `src/otm_workbench/models.py`:

```python
class LoadPlanCutoverReadiness(Base, TimestampMixin):
    __tablename__ = "load_plan_cutover_readiness"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    package_id: Mapped[str] = mapped_column(ForeignKey("load_plan_packages.id"), index=True)
    sequence_snapshot_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String, default="MISSING_SEQUENCE", index=True)
    readiness_json: Mapped[str] = mapped_column(Text, default="{}")
    blockers_json: Mapped[str] = mapped_column(Text, default="[]")
    summary_json: Mapped[str] = mapped_column(Text, default="{}")
    evidence_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    generated_by: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
```

- [ ] **Step 4: Add the Alembic migration**

Create `migrations/versions/a8d3e5f7b2c1_load_plan_cutover_readiness.py`:

```python
"""load plan cutover readiness

Revision ID: a8d3e5f7b2c1
Revises: f2a6c8d1e9b4
Create Date: 2026-05-18 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "a8d3e5f7b2c1"
down_revision: str | None = "f2a6c8d1e9b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "load_plan_cutover_readiness",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("environment_id", sa.String(), nullable=True),
        sa.Column("profile_id", sa.String(), nullable=True),
        sa.Column("package_id", sa.String(), nullable=False),
        sa.Column("sequence_snapshot_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("readiness_json", sa.Text(), nullable=False),
        sa.Column("blockers_json", sa.Text(), nullable=False),
        sa.Column("summary_json", sa.Text(), nullable=False),
        sa.Column("evidence_id", sa.String(), nullable=True),
        sa.Column("generated_by", sa.String(), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
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
        "sequence_snapshot_id",
        "status",
        "evidence_id",
        "generated_by",
        "generated_at",
    ]:
        op.create_index(
            f"ix_load_plan_cutover_readiness_{column}",
            "load_plan_cutover_readiness",
            [column],
        )


def downgrade() -> None:
    for column in [
        "generated_at",
        "generated_by",
        "evidence_id",
        "status",
        "sequence_snapshot_id",
        "package_id",
        "profile_id",
        "environment_id",
        "project_id",
    ]:
        op.drop_index(f"ix_load_plan_cutover_readiness_{column}", table_name="load_plan_cutover_readiness")
    op.drop_table("load_plan_cutover_readiness")
```

- [ ] **Step 5: Run the table test again**

Run:

```powershell
python -m pytest tests/test_load_plan_cutover_readiness.py::test_load_plan_cutover_readiness_table_exists_after_metadata_reset -q
```

Expected: pass.

- [ ] **Step 6: Commit persistence**

```powershell
git add src/otm_workbench/models.py migrations/versions/a8d3e5f7b2c1_load_plan_cutover_readiness.py tests/test_load_plan_cutover_readiness.py
git commit -m "feat: add load plan cutover readiness model"
```

---

### Task 2: Readiness Service And Generate Endpoint

**Files:**
- Create: `src/otm_workbench/modules/load_plan/readiness.py`
- Modify: `src/otm_workbench/modules/load_plan/routes.py`
- Modify: `tests/test_load_plan_cutover_readiness.py`

- [ ] **Step 1: Add failing generation tests**

Append to `tests/test_load_plan_cutover_readiness.py`:

```python
def test_cutover_readiness_generate_rejects_missing_package(client, admin_header):
    response = client.post(
        "/api/v1/modules/load-plan/cutover-readiness/generate",
        json={"package_id": "missing_package"},
        headers=admin_header,
    )

    assert response.status_code == 404


def test_cutover_readiness_missing_sequence_snapshot(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)

    response = client.post(
        "/api/v1/modules/load-plan/cutover-readiness/generate",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["package_count"] == 1
    item = payload["items"][0]
    assert item["package_id"] == package["id"]
    assert item["sequence_snapshot_id"] is None
    assert item["status"] == "MISSING_SEQUENCE"
    assert item["blockers"][0]["code"] == "SEQUENCE_SNAPSHOT_MISSING"
    assert "generate_sequence_snapshot" in payload["summary"]["next_actions"]
```

- [ ] **Step 2: Run the failing tests**

Run:

```powershell
python -m pytest tests/test_load_plan_cutover_readiness.py::test_cutover_readiness_generate_rejects_missing_package tests/test_load_plan_cutover_readiness.py::test_cutover_readiness_missing_sequence_snapshot -q
```

Expected: fail because the route does not exist.

- [ ] **Step 3: Implement readiness service**

Create `src/otm_workbench/modules/load_plan/readiness.py`:

```python
import json

from sqlalchemy.orm import Session

from otm_workbench.models import (
    AuditLog,
    DomainEvent,
    Evidence,
    LoadPlanCutoverReadiness,
    LoadPlanPackage,
    LoadPlanSequenceSnapshot,
    utcnow,
)
from otm_workbench.modules.load_plan.packages import parse_json_list, parse_json_object
from otm_workbench.modules.load_plan.sequence import latest_sequence_snapshot


READY_STATUS = "READY"
BLOCKED_STATUS = "BLOCKED"
NEEDS_REVIEW_STATUS = "NEEDS_REVIEW"
MISSING_SEQUENCE_STATUS = "MISSING_SEQUENCE"


def readiness_blocker(code: str, severity: str, message: str, *, source_type: str | None = None, source_id: str | None = None) -> dict[str, object]:
    return {
        "code": code,
        "severity": severity,
        "table_name": None,
        "source_type": source_type,
        "source_id": source_id,
        "message": message,
        "details": {},
    }


def readiness_status_from_blockers(blockers: list[dict[str, object]], sequence_snapshot: LoadPlanSequenceSnapshot | None) -> str:
    if sequence_snapshot is None:
        return MISSING_SEQUENCE_STATUS
    if any(item.get("severity") == "ERROR" for item in blockers):
        return BLOCKED_STATUS
    if blockers:
        return NEEDS_REVIEW_STATUS
    return READY_STATUS


def readiness_checks(status: str, sequence_snapshot: LoadPlanSequenceSnapshot | None, blockers: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "code": "SEQUENCE_SNAPSHOT_AVAILABLE",
            "status": "PASSED" if sequence_snapshot is not None else "FAILED",
            "message": "Latest sequence snapshot is available." if sequence_snapshot is not None else "Generate a sequence snapshot first.",
        },
        {
            "code": "NO_ERROR_BLOCKERS",
            "status": "PASSED" if not any(item.get("severity") == "ERROR" for item in blockers) else "FAILED",
            "message": "No error blockers were found." if status != BLOCKED_STATUS else "Latest sequence snapshot contains error blockers.",
        },
        {
            "code": "NO_WARNING_BLOCKERS",
            "status": "PASSED" if not any(item.get("severity") == "WARNING" for item in blockers) else "REVIEW",
            "message": "No warning blockers were found." if status != NEEDS_REVIEW_STATUS else "Latest sequence snapshot contains warning blockers.",
        },
    ]


def next_actions_for_status(status: str) -> list[str]:
    if status == MISSING_SEQUENCE_STATUS:
        return ["generate_sequence_snapshot"]
    if status == BLOCKED_STATUS:
        return ["resolve_sequence_blockers"]
    if status == NEEDS_REVIEW_STATUS:
        return ["review_warnings"]
    return ["ready_for_cutover_export"]


def serialize_cutover_readiness(readiness: LoadPlanCutoverReadiness) -> dict[str, object]:
    return {
        "id": readiness.id,
        "project_id": readiness.project_id,
        "environment_id": readiness.environment_id,
        "profile_id": readiness.profile_id,
        "package_id": readiness.package_id,
        "sequence_snapshot_id": readiness.sequence_snapshot_id,
        "status": readiness.status,
        "readiness": parse_json_object(readiness.readiness_json),
        "blockers": parse_json_list(readiness.blockers_json),
        "summary": parse_json_object(readiness.summary_json),
        "evidence_id": readiness.evidence_id,
        "generated_by": readiness.generated_by,
        "generated_at": readiness.generated_at.isoformat() if readiness.generated_at else None,
    }


def latest_cutover_readiness(db: Session, package_id: str) -> LoadPlanCutoverReadiness | None:
    return (
        db.query(LoadPlanCutoverReadiness)
        .filter(LoadPlanCutoverReadiness.package_id == package_id)
        .order_by(LoadPlanCutoverReadiness.generated_at.desc(), LoadPlanCutoverReadiness.created_at.desc())
        .first()
    )


def summarize_readiness(items: list[LoadPlanCutoverReadiness]) -> dict[str, object]:
    blockers = [blocker for item in items for blocker in parse_json_list(item.blockers_json)]
    statuses = [item.status for item in items]
    error_count = sum(1 for item in blockers if item.get("severity") == "ERROR")
    warning_count = sum(1 for item in blockers if item.get("severity") == "WARNING")
    next_actions: list[str] = []
    for status in [MISSING_SEQUENCE_STATUS, BLOCKED_STATUS, NEEDS_REVIEW_STATUS, READY_STATUS]:
        if status in statuses:
            for action in next_actions_for_status(status):
                if action not in next_actions:
                    next_actions.append(action)
    return {
        "package_count": len(items),
        "ready_count": statuses.count(READY_STATUS),
        "blocked_count": statuses.count(BLOCKED_STATUS),
        "needs_review_count": statuses.count(NEEDS_REVIEW_STATUS),
        "missing_sequence_count": statuses.count(MISSING_SEQUENCE_STATUS),
        "blocker_count": len(blockers),
        "error_count": error_count,
        "warning_count": warning_count,
        "next_actions": next_actions,
    }


def generate_readiness_for_package(db: Session, *, package: LoadPlanPackage, generated_by: str) -> LoadPlanCutoverReadiness:
    sequence_snapshot = latest_sequence_snapshot(db, package.id)
    blockers = (
        [
            readiness_blocker(
                "SEQUENCE_SNAPSHOT_MISSING",
                "ERROR",
                "No sequence snapshot exists for this package.",
                source_type="load_plan_package",
                source_id=package.id,
            )
        ]
        if sequence_snapshot is None
        else parse_json_list(sequence_snapshot.blockers_json)
    )
    status = readiness_status_from_blockers(blockers, sequence_snapshot)
    readiness_payload = {
        "package_id": package.id,
        "sequence_snapshot_id": sequence_snapshot.id if sequence_snapshot is not None else None,
        "status": status,
        "checks": readiness_checks(status, sequence_snapshot, blockers),
    }
    summary = summarize_readiness_stub(status, blockers)
    generated_at = utcnow()
    readiness = LoadPlanCutoverReadiness(
        project_id=package.project_id,
        environment_id=package.environment_id,
        profile_id=package.profile_id,
        package_id=package.id,
        sequence_snapshot_id=sequence_snapshot.id if sequence_snapshot is not None else None,
        status=status,
        readiness_json=json.dumps(readiness_payload, sort_keys=True),
        blockers_json=json.dumps(blockers, sort_keys=True),
        summary_json=json.dumps(summary, sort_keys=True),
        generated_by=generated_by,
        generated_at=generated_at,
    )
    db.add(readiness)
    db.flush()
    evidence_summary = {
        "source_entity_type": "load_plan_cutover_readiness",
        "source_entity_id": readiness.id,
        "package_id": package.id,
        "sequence_snapshot_id": readiness.sequence_snapshot_id,
        "status": status,
        "blocker_count": summary["blocker_count"],
        "error_count": summary["error_count"],
        "warning_count": summary["warning_count"],
    }
    evidence = Evidence(
        project_id=package.project_id,
        source_module="load_plan",
        evidence_type="load_plan_cutover_readiness",
        summary_json=json.dumps(evidence_summary, sort_keys=True),
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db.add(evidence)
    db.flush()
    readiness.evidence_id = evidence.id
    db.add(
        AuditLog(
            actor_user_id=generated_by,
            action="load_plan.cutover_readiness.generate",
            target_type="load_plan_cutover_readiness",
            target_id=readiness.id,
            metadata_json=json.dumps(
                {
                    "package_id": package.id,
                    "sequence_snapshot_id": readiness.sequence_snapshot_id,
                    "status": status,
                    "evidence_id": evidence.id,
                    "blocker_count": summary["blocker_count"],
                },
                sort_keys=True,
            ),
        )
    )
    db.add(
        DomainEvent(
            event_type="load_plan.cutover_readiness.generated",
            source_module="load_plan",
            project_id=package.project_id,
            aggregate_type="load_plan_cutover_readiness",
            aggregate_id=readiness.id,
            payload_json=json.dumps({"package_id": package.id, "status": status}, sort_keys=True),
            status="PENDING",
        )
    )
    db.flush()
    return readiness


def summarize_readiness_stub(status: str, blockers: list[dict[str, object]]) -> dict[str, object]:
    error_count = sum(1 for item in blockers if item.get("severity") == "ERROR")
    warning_count = sum(1 for item in blockers if item.get("severity") == "WARNING")
    return {
        "package_count": 1,
        "ready_count": 1 if status == READY_STATUS else 0,
        "blocked_count": 1 if status == BLOCKED_STATUS else 0,
        "needs_review_count": 1 if status == NEEDS_REVIEW_STATUS else 0,
        "missing_sequence_count": 1 if status == MISSING_SEQUENCE_STATUS else 0,
        "blocker_count": len(blockers),
        "error_count": error_count,
        "warning_count": warning_count,
        "next_actions": next_actions_for_status(status),
    }


def generate_cutover_readiness(
    db: Session,
    *,
    packages: list[LoadPlanPackage],
    generated_by: str,
) -> dict[str, object]:
    if not packages:
        raise ValueError("At least one registered Load Plan package is required for cutover readiness generation.")
    items = [generate_readiness_for_package(db, package=package, generated_by=generated_by) for package in packages]
    db.commit()
    for item in items:
        db.refresh(item)
    return {
        "items": [serialize_cutover_readiness(item) for item in items],
        "summary": summarize_readiness(items),
    }
```

- [ ] **Step 4: Add generate route**

Modify `src/otm_workbench/modules/load_plan/routes.py`:

```python
from otm_workbench.models import (
    CsvutilBuild,
    LoadPlanCutoverReadiness,
    LoadPlanPackage,
    LoadPlanReviewItem,
    LoadPlanSequenceSnapshot,
    LoadPlanZipAnalysis,
    RateBatch,
    User,
)
from otm_workbench.modules.load_plan.readiness import (
    generate_cutover_readiness,
    latest_cutover_readiness,
    serialize_cutover_readiness,
)
```

Add request model:

```python
class CutoverReadinessGenerateRequest(BaseModel):
    package_id: str | None = None
```

Add route after sequence routes:

```python
@router.post("/cutover-readiness/generate")
def generate_load_plan_cutover_readiness(
    payload: CutoverReadinessGenerateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    if payload.package_id:
        package = db.query(LoadPlanPackage).filter(LoadPlanPackage.id == payload.package_id).first()
        if package is None:
            raise HTTPException(status_code=404, detail="Load Plan package not found.")
        packages = [package]
    else:
        packages = db.query(LoadPlanPackage).order_by(LoadPlanPackage.created_at).all()
    try:
        return generate_cutover_readiness(db, packages=packages, generated_by=user.email)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
```

- [ ] **Step 5: Run focused generation tests**

Run:

```powershell
python -m pytest tests/test_load_plan_cutover_readiness.py::test_cutover_readiness_generate_rejects_missing_package tests/test_load_plan_cutover_readiness.py::test_cutover_readiness_missing_sequence_snapshot -q
```

Expected: pass.

- [ ] **Step 6: Commit generation**

```powershell
git add src/otm_workbench/modules/load_plan/readiness.py src/otm_workbench/modules/load_plan/routes.py tests/test_load_plan_cutover_readiness.py
git commit -m "feat: generate load plan cutover readiness"
```

---

### Task 3: Status Derivation And Safety Tests

**Files:**
- Modify: `tests/test_load_plan_cutover_readiness.py`
- Modify: `src/otm_workbench/modules/load_plan/readiness.py` only if tests expose a defect.

- [ ] **Step 1: Add status tests for blocked and ready snapshots**

Append:

```python
def test_cutover_readiness_blocked_from_blocked_sequence_snapshot(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    snapshot = create_sequence_snapshot(client, admin_header, package)

    response = client.post(
        "/api/v1/modules/load-plan/cutover-readiness/generate",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["sequence_snapshot_id"] == snapshot["id"]
    assert item["status"] == "BLOCKED"
    assert item["summary"]["error_count"] > 0
    assert "resolve_sequence_blockers" in response.json()["summary"]["next_actions"]


def test_cutover_readiness_ready_from_blocker_free_sequence_snapshot(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    package_model = db_session.query(LoadPlanPackage).filter(LoadPlanPackage.id == package["id"]).one()
    snapshot = LoadPlanSequenceSnapshot(
        project_id=package_model.project_id,
        environment_id=package_model.environment_id,
        profile_id=package_model.profile_id,
        package_id=package["id"],
        status="READY_FOR_REVIEW",
        sequence_json=json.dumps(
            [{"position": 1, "table_name": "ACCESSORIAL_COST", "row_count": 1, "requirement_level": "OPTIONAL"}],
            sort_keys=True,
        ),
        blockers_json="[]",
        summary_json=json.dumps({"blocker_count": 0, "error_count": 0, "warning_count": 0}, sort_keys=True),
        generated_by="admin@example.com",
    )
    db_session.add(snapshot)
    db_session.commit()

    response = client.post(
        "/api/v1/modules/load-plan/cutover-readiness/generate",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["sequence_snapshot_id"] == snapshot.id
    assert item["status"] == "READY"
    assert "ready_for_cutover_export" in response.json()["summary"]["next_actions"]
```

- [ ] **Step 2: Add warning-only and metadata safety tests**

Append:

```python
def test_cutover_readiness_needs_review_from_warning_only_sequence_snapshot(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    package_model = db_session.query(LoadPlanPackage).filter(LoadPlanPackage.id == package["id"]).one()
    snapshot = LoadPlanSequenceSnapshot(
        project_id=package_model.project_id,
        environment_id=package_model.environment_id,
        profile_id=package_model.profile_id,
        package_id=package["id"],
        status="BLOCKED",
        sequence_json="[]",
        blockers_json=json.dumps(
            [
                {
                    "code": "REVIEW_ITEM_EXCLUDED_FROM_CUTOVER",
                    "severity": "WARNING",
                    "table_name": "ACCESSORIAL_COST",
                    "source_type": "load_plan_review_decision",
                    "source_id": "synthetic_decision",
                    "message": "Synthetic exclusion requires review.",
                    "details": {},
                }
            ],
            sort_keys=True,
        ),
        summary_json=json.dumps({"blocker_count": 1, "error_count": 0, "warning_count": 1}, sort_keys=True),
        generated_by="admin@example.com",
    )
    db_session.add(snapshot)
    db_session.commit()

    response = client.post(
        "/api/v1/modules/load-plan/cutover-readiness/generate",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["status"] == "NEEDS_REVIEW"
    assert item["summary"]["warning_count"] == 1
    assert "review_warnings" in response.json()["summary"]["next_actions"]


def test_cutover_readiness_creates_evidence_audit_event_without_raw_values(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    rewrite_export_with_unknown_column(db_session, export)
    snapshot = create_sequence_snapshot(client, admin_header, package)

    response = client.post(
        "/api/v1/modules/load-plan/cutover-readiness/generate",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    readiness = db_session.query(LoadPlanCutoverReadiness).filter(LoadPlanCutoverReadiness.id == response.json()["items"][0]["id"]).one()
    evidence = db_session.query(Evidence).filter(Evidence.id == readiness.evidence_id).one()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "load_plan.cutover_readiness.generate").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "load_plan.cutover_readiness.generated").one()
    assert evidence.evidence_type == "load_plan_cutover_readiness"
    assert evidence.client_safe is True
    assert audit.target_id == readiness.id
    assert event.aggregate_id == readiness.id
    assert "OTM1.ACC_COST_001" not in evidence.summary_json
    assert "OTM1.ACC_COST_001" not in audit.metadata_json
    assert "OTM1.ACC_COST_001" not in event.payload_json
    assert "Synthetic" not in evidence.summary_json
```

- [ ] **Step 3: Run status and safety tests**

Run:

```powershell
python -m pytest tests/test_load_plan_cutover_readiness.py::test_cutover_readiness_blocked_from_blocked_sequence_snapshot tests/test_load_plan_cutover_readiness.py::test_cutover_readiness_ready_from_blocker_free_sequence_snapshot tests/test_load_plan_cutover_readiness.py::test_cutover_readiness_needs_review_from_warning_only_sequence_snapshot tests/test_load_plan_cutover_readiness.py::test_cutover_readiness_creates_evidence_audit_event_without_raw_values -q
```

Expected: pass.

- [ ] **Step 4: Commit status behavior**

```powershell
git add src/otm_workbench/modules/load_plan/readiness.py tests/test_load_plan_cutover_readiness.py
git commit -m "feat: derive load plan readiness statuses"
```

---

### Task 4: List, Detail, Latest, Aggregate Generation, README

**Files:**
- Modify: `src/otm_workbench/modules/load_plan/routes.py`
- Modify: `tests/test_load_plan_cutover_readiness.py`
- Modify: `README.md`

- [ ] **Step 1: Add route and aggregate tests**

Append:

```python
def test_cutover_readiness_list_detail_latest_and_filters(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    create_sequence_snapshot(client, admin_header, package)
    created = client.post(
        "/api/v1/modules/load-plan/cutover-readiness/generate",
        json={"package_id": package["id"]},
        headers=admin_header,
    ).json()["items"][0]

    listed = client.get("/api/v1/modules/load-plan/cutover-readiness", headers=admin_header)
    filtered = client.get(
        "/api/v1/modules/load-plan/cutover-readiness",
        params={"package_id": package["id"], "status": "BLOCKED"},
        headers=admin_header,
    )
    detail = client.get(f"/api/v1/modules/load-plan/cutover-readiness/{created['id']}", headers=admin_header)
    latest = client.get(
        "/api/v1/modules/load-plan/cutover-readiness/latest",
        params={"package_id": package["id"]},
        headers=admin_header,
    )

    assert listed.status_code == 200
    assert filtered.status_code == 200
    assert detail.status_code == 200
    assert latest.status_code == 200
    assert listed.json()["total"] == 1
    assert filtered.json()["items"][0]["id"] == created["id"]
    assert detail.json()["id"] == created["id"]
    assert latest.json()["id"] == created["id"]


def test_cutover_readiness_aggregate_generation(client, admin_header, db_session):
    first_batch, first_export, first_approval, first_package = prepare_registered_load_plan_package(client, admin_header)
    second_batch = create_rate_batch(client, admin_header, scenario_code="ACCESSORIAL_ONLY")
    add_accessorial_table(client, admin_header, second_batch["id"], xid="ACC_COST_002")
    preview = client.post(f"/api/v1/modules/rates/batches/{second_batch['id']}/csv-preview", headers=admin_header)
    assert preview.status_code == 200
    second_export = client.post(f"/api/v1/modules/rates/batches/{second_batch['id']}/export-csv", headers=admin_header)
    assert second_export.status_code == 200
    second_approval = client.post(
        f"/api/v1/modules/rates/batches/{second_batch['id']}/approve",
        json={"approval_note": "Reviewed for second synthetic readiness package"},
        headers=admin_header,
    )
    assert second_approval.status_code == 200
    second_package = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{second_batch['id']}",
        headers=admin_header,
    )
    assert second_package.status_code == 200

    response = client.post(
        "/api/v1/modules/load-plan/cutover-readiness/generate",
        json={},
        headers=admin_header,
    )

    assert response.status_code == 200
    assert response.json()["summary"]["package_count"] == 2
    assert len(response.json()["items"]) == 2
    assert db_session.query(LoadPlanCutoverReadiness).count() == 2
```

- [ ] **Step 2: Add list/detail/latest routes**

Modify `src/otm_workbench/modules/load_plan/routes.py` and add after generate route:

```python
@router.get("/cutover-readiness")
def list_cutover_readiness(
    package_id: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    query = db.query(LoadPlanCutoverReadiness)
    if package_id:
        query = query.filter(LoadPlanCutoverReadiness.package_id == package_id)
    if status:
        query = query.filter(LoadPlanCutoverReadiness.status == status)
    items = query.order_by(LoadPlanCutoverReadiness.generated_at.desc()).all()
    return PageResponse(items=[serialize_cutover_readiness(item) for item in items], total=len(items))


@router.get("/cutover-readiness/latest")
def get_latest_cutover_readiness(
    package_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    readiness = latest_cutover_readiness(db, package_id)
    if readiness is None:
        raise HTTPException(status_code=404, detail="Load Plan cutover readiness not found.")
    return serialize_cutover_readiness(readiness)


@router.get("/cutover-readiness/{readiness_id}")
def get_cutover_readiness(
    readiness_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    readiness = db.query(LoadPlanCutoverReadiness).filter(LoadPlanCutoverReadiness.id == readiness_id).first()
    if readiness is None:
        raise HTTPException(status_code=404, detail="Load Plan cutover readiness not found.")
    return serialize_cutover_readiness(readiness)
```

Place `/cutover-readiness/latest` before `/cutover-readiness/{readiness_id}` so FastAPI does not treat `latest` as an id.

- [ ] **Step 3: Run route tests**

Run:

```powershell
python -m pytest tests/test_load_plan_cutover_readiness.py::test_cutover_readiness_list_detail_latest_and_filters tests/test_load_plan_cutover_readiness.py::test_cutover_readiness_aggregate_generation -q
```

Expected: pass.

- [ ] **Step 4: Update README**

Add after the Load Plan Sequence Blockers paragraph:

```markdown
The Load Plan Cutover Readiness slice generates backend-only readiness records
from the latest sequence snapshots, preserving client-safe blockers, evidence,
audit, and domain events. It does not export cutover packages, execute CSVUTIL,
connect to OTM, or transition package status.
```

Extend the verification command:

```powershell
python -m pytest tests/test_reference_catalog.py tests/test_rates_dictionary.py tests/test_rates_csv_preview.py tests/test_rates_batch_approval.py tests/test_load_plan_package_intake.py tests/test_load_plan_csvutil_builder.py tests/test_load_plan_zip_analysis.py tests/test_load_plan_review_queue.py tests/test_load_plan_review_decisions.py tests/test_load_plan_sequence_blockers.py tests/test_load_plan_cutover_readiness.py
```

- [ ] **Step 5: Run focused readiness tests**

Run:

```powershell
python -m pytest tests/test_load_plan_cutover_readiness.py -q
```

Expected: all readiness tests pass.

- [ ] **Step 6: Commit routes and README**

```powershell
git add src/otm_workbench/modules/load_plan/routes.py README.md tests/test_load_plan_cutover_readiness.py
git commit -m "feat: expose load plan cutover readiness"
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
- Alembic upgrades through `a8d3e5f7b2c1`.
- Ruff reports `All checks passed!`.

- [ ] **Step 2: Inspect git status**

Run:

```powershell
git status --short --branch
```

Expected:

```text
## codex/load-plan-cutover-readiness
?? OTM_RESOURCES/
```

`OTM_RESOURCES/` must remain untracked.

- [ ] **Step 3: Push branch**

```powershell
git push -u origin codex/load-plan-cutover-readiness
```

- [ ] **Step 4: Open PR**

Use GitHub connector.

Title:

```text
Load Plan Cutover Readiness
```

Body:

```markdown
## Summary
- Add Load Plan cutover readiness persistence and migration.
- Generate readiness from latest sequence snapshots without recalculating blockers.
- Add generate/list/detail/latest APIs with client-safe evidence, audit, and domain events.

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
git branch -d codex/load-plan-cutover-readiness
git status --short --branch
```

Expected: `main` is current and only `OTM_RESOURCES/` is untracked.

---

## Self-Review Checklist

- Spec coverage: persistence, generation, statuses, aggregate response, list/detail/latest routes, evidence/audit/event, tests, README, and exclusions are covered.
- Placeholder scan: no deferred implementation text is present; all steps include concrete files, snippets, and commands.
- Type consistency: model `LoadPlanCutoverReadiness`, table `load_plan_cutover_readiness`, route prefix `/cutover-readiness`, statuses, action, event, and evidence type match the design spec.
- Data safety: examples use synthetic `OTM1`/`DEMO`; evidence/audit/events avoid raw row values and decision notes.
