# Load Plan Package Intake Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add backend/API support for registering approved Rates CSV exports as Load Plan packages.

**Architecture:** Add a small `LoadPlanPackage` model and migration, then implement a focused `modules/load_plan/packages.py` service for Rates intake, serialization, summary counts, and idempotency. Expose thin FastAPI routes under `/api/v1/modules/load-plan` and keep package metadata client-safe by linking artifacts, manifests, and evidence instead of copying payloads.

**Tech Stack:** Python, FastAPI, SQLAlchemy, Alembic, SQLite, pytest, Ruff.

---

## File Structure

- Modify `src/otm_workbench/models.py`: add `LoadPlanPackage`.
- Create `migrations/versions/d2f7b9c4a8e3_load_plan_package_intake.py`: create/drop `load_plan_packages`.
- Create `src/otm_workbench/modules/load_plan/__init__.py`: package marker.
- Create `src/otm_workbench/modules/load_plan/packages.py`: intake service, serializers, summary logic.
- Create `src/otm_workbench/modules/load_plan/routes.py`: API routes.
- Modify `src/otm_workbench/main.py`: include the Load Plan router.
- Modify `src/otm_workbench/platform/navigation.py`: seed `load_plan` module.
- Create `tests/test_load_plan_package_intake.py`: end-to-end API and persistence tests.
- Modify `README.md`: mention Load Plan package intake verification.

No UI, CSVUTIL, ZIP analysis, setup review, cutover readiness, or real OTM load is included.

Before implementing, confirm the OTM table assumptions against `OTM_RESOURCES/DATA_DICT26B/data_dictionary/json/data_dict`. Test data must use synthetic `OTM1` values only.

---

## Task 1: Model And Migration

**Files:**
- Modify: `src/otm_workbench/models.py`
- Create: `migrations/versions/d2f7b9c4a8e3_load_plan_package_intake.py`
- Test: `tests/test_load_plan_package_intake.py`

- [ ] **Step 1: Write failing migration/model test**

Create `tests/test_load_plan_package_intake.py`:

```python
import json

from sqlalchemy import inspect

from otm_workbench.database import engine
from otm_workbench.models import AuditLog, DomainEvent, Evidence, LoadPlanPackage


def create_rate_batch(client, admin_header, scenario_code="ACCESSORIAL_ONLY"):
    response = client.post(
        "/api/v1/modules/rates/batches",
        json={"scenario_code": scenario_code, "name": "Synthetic load package batch", "domain_name": "OTM1"},
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


def prepare_approved_exported_rate_batch(client, admin_header):
    batch = create_rate_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])
    preview = client.post(f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview", headers=admin_header)
    assert preview.status_code == 200
    export = client.post(f"/api/v1/modules/rates/batches/{batch['id']}/export-csv", headers=admin_header)
    assert export.status_code == 200
    approval = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/approve",
        json={"approval_note": "Reviewed for synthetic load package"},
        headers=admin_header,
    )
    assert approval.status_code == 200
    return batch, export.json(), approval.json()


def test_load_plan_packages_table_exists_after_metadata_reset():
    tables = set(inspect(engine).get_table_names())

    assert "load_plan_packages" in tables
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
python -m pytest tests/test_load_plan_package_intake.py::test_load_plan_packages_table_exists_after_metadata_reset -q
```

Expected: FAIL because `LoadPlanPackage` and `load_plan_packages` do not exist.

- [ ] **Step 3: Add `LoadPlanPackage` model**

In `src/otm_workbench/models.py`, after `RateBatchIssue`, add:

```python
class LoadPlanPackage(Base, TimestampMixin):
    __tablename__ = "load_plan_packages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    source_module: Mapped[str] = mapped_column(String, index=True)
    source_entity_type: Mapped[str] = mapped_column(String, index=True)
    source_entity_id: Mapped[str] = mapped_column(String, index=True)
    package_type: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, default="REGISTERED", index=True)
    artifact_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    manifest_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    evidence_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    approval_evidence_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    load_sequence_json: Mapped[str] = mapped_column(Text, default="[]")
    summary_json: Mapped[str] = mapped_column(Text, default="{}")
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
```

- [ ] **Step 4: Add migration**

Create `migrations/versions/d2f7b9c4a8e3_load_plan_package_intake.py`:

```python
"""load plan package intake

Revision ID: d2f7b9c4a8e3
Revises: c9f2a8d4e6b1
Create Date: 2026-05-18 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d2f7b9c4a8e3"
down_revision: Union[str, None] = "c9f2a8d4e6b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "load_plan_packages",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("environment_id", sa.String(), nullable=True),
        sa.Column("profile_id", sa.String(), nullable=True),
        sa.Column("source_module", sa.String(), nullable=False),
        sa.Column("source_entity_type", sa.String(), nullable=False),
        sa.Column("source_entity_id", sa.String(), nullable=False),
        sa.Column("package_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("artifact_id", sa.String(), nullable=True),
        sa.Column("manifest_id", sa.String(), nullable=True),
        sa.Column("evidence_id", sa.String(), nullable=True),
        sa.Column("approval_evidence_id", sa.String(), nullable=True),
        sa.Column("load_sequence_json", sa.Text(), nullable=False),
        sa.Column("summary_json", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("registered_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_load_plan_packages_project_id"), "load_plan_packages", ["project_id"])
    op.create_index(op.f("ix_load_plan_packages_environment_id"), "load_plan_packages", ["environment_id"])
    op.create_index(op.f("ix_load_plan_packages_profile_id"), "load_plan_packages", ["profile_id"])
    op.create_index(op.f("ix_load_plan_packages_source_module"), "load_plan_packages", ["source_module"])
    op.create_index(op.f("ix_load_plan_packages_source_entity_type"), "load_plan_packages", ["source_entity_type"])
    op.create_index(op.f("ix_load_plan_packages_source_entity_id"), "load_plan_packages", ["source_entity_id"])
    op.create_index(op.f("ix_load_plan_packages_package_type"), "load_plan_packages", ["package_type"])
    op.create_index(op.f("ix_load_plan_packages_status"), "load_plan_packages", ["status"])
    op.create_index(op.f("ix_load_plan_packages_artifact_id"), "load_plan_packages", ["artifact_id"])
    op.create_index(op.f("ix_load_plan_packages_manifest_id"), "load_plan_packages", ["manifest_id"])
    op.create_index(op.f("ix_load_plan_packages_evidence_id"), "load_plan_packages", ["evidence_id"])
    op.create_index(
        op.f("ix_load_plan_packages_approval_evidence_id"),
        "load_plan_packages",
        ["approval_evidence_id"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_load_plan_packages_approval_evidence_id"), table_name="load_plan_packages")
    op.drop_index(op.f("ix_load_plan_packages_evidence_id"), table_name="load_plan_packages")
    op.drop_index(op.f("ix_load_plan_packages_manifest_id"), table_name="load_plan_packages")
    op.drop_index(op.f("ix_load_plan_packages_artifact_id"), table_name="load_plan_packages")
    op.drop_index(op.f("ix_load_plan_packages_status"), table_name="load_plan_packages")
    op.drop_index(op.f("ix_load_plan_packages_package_type"), table_name="load_plan_packages")
    op.drop_index(op.f("ix_load_plan_packages_source_entity_id"), table_name="load_plan_packages")
    op.drop_index(op.f("ix_load_plan_packages_source_entity_type"), table_name="load_plan_packages")
    op.drop_index(op.f("ix_load_plan_packages_source_module"), table_name="load_plan_packages")
    op.drop_index(op.f("ix_load_plan_packages_profile_id"), table_name="load_plan_packages")
    op.drop_index(op.f("ix_load_plan_packages_environment_id"), table_name="load_plan_packages")
    op.drop_index(op.f("ix_load_plan_packages_project_id"), table_name="load_plan_packages")
    op.drop_table("load_plan_packages")
```

- [ ] **Step 5: Run model test**

Run:

```bash
python -m pytest tests/test_load_plan_package_intake.py::test_load_plan_packages_table_exists_after_metadata_reset -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add src/otm_workbench/models.py migrations/versions/d2f7b9c4a8e3_load_plan_package_intake.py tests/test_load_plan_package_intake.py
git commit -m "feat: add load plan package model"
```

---

## Task 2: Register Rates Package Intake

**Files:**
- Create: `src/otm_workbench/modules/load_plan/__init__.py`
- Create: `src/otm_workbench/modules/load_plan/packages.py`
- Create: `src/otm_workbench/modules/load_plan/routes.py`
- Modify: `src/otm_workbench/main.py`
- Test: `tests/test_load_plan_package_intake.py`

- [ ] **Step 1: Add failing intake tests**

Append to `tests/test_load_plan_package_intake.py`:

```python
def test_register_rejects_unapproved_rate_batch(client, admin_header):
    batch = create_rate_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])
    client.post(f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview", headers=admin_header)
    export = client.post(f"/api/v1/modules/rates/batches/{batch['id']}/export-csv", headers=admin_header)
    assert export.status_code == 200

    response = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "approved" in response.json()["message"].lower()


def test_register_rejects_approved_rate_batch_without_export(client, admin_header):
    batch = create_rate_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])
    client.post(f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview", headers=admin_header)
    approval = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/approve",
        json={"approval_note": "Approved without export for negative test"},
        headers=admin_header,
    )
    assert approval.status_code == 200

    response = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "export" in response.json()["message"].lower()


def test_register_rates_package_creates_load_plan_package(client, admin_header, db_session):
    batch, export, approval = prepare_approved_exported_rate_batch(client, admin_header)

    response = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    package = db_session.query(LoadPlanPackage).filter(LoadPlanPackage.id == payload["id"]).one()
    assert payload["source_module"] == "rates"
    assert payload["source_entity_type"] == "rate_batch"
    assert payload["source_entity_id"] == batch["id"]
    assert payload["package_type"] == "rates_csv_zip"
    assert payload["status"] == "REGISTERED"
    assert payload["artifact_id"] == export["artifact_id"]
    assert payload["manifest_id"] == export["manifest_id"]
    assert payload["approval_evidence_id"] == approval["evidence_id"]
    assert payload["load_sequence"] == [
        {
            "position": 6,
            "table_name": "ACCESSORIAL_COST",
            "row_count": 1,
            "requirement_level": "REQUIRED",
        }
    ]
    assert package.created_by == "admin@example.com"
    assert package.registered_at is not None
```

- [ ] **Step 2: Run intake tests to verify failure**

Run:

```bash
python -m pytest tests/test_load_plan_package_intake.py::test_register_rejects_unapproved_rate_batch tests/test_load_plan_package_intake.py::test_register_rejects_approved_rate_batch_without_export tests/test_load_plan_package_intake.py::test_register_rates_package_creates_load_plan_package -q
```

Expected: FAIL because the Load Plan router/service does not exist.

- [ ] **Step 3: Create package marker**

Create `src/otm_workbench/modules/load_plan/__init__.py`:

```python
"""Load Plan module foundation."""
```

- [ ] **Step 4: Implement package intake service**

Create `src/otm_workbench/modules/load_plan/packages.py`:

```python
import json

from sqlalchemy.orm import Session

from otm_workbench.models import (
    AuditLog,
    DomainEvent,
    Evidence,
    LoadPlanPackage,
    RateBatch,
    RateBatchTable,
    utcnow,
)
from otm_workbench.modules.rates.approval import get_existing_approval_evidence
from otm_workbench.modules.rates.exports import list_batch_export_evidence


def parse_json_object(value: str | None) -> dict[str, object]:
    if not value:
        return {}
    parsed = json.loads(value)
    return parsed if isinstance(parsed, dict) else {}


def parse_json_list(value: str | None) -> list[dict[str, object]]:
    if not value:
        return []
    parsed = json.loads(value)
    return parsed if isinstance(parsed, list) else []


def serialize_load_plan_package(package: LoadPlanPackage) -> dict[str, object]:
    return {
        "id": package.id,
        "project_id": package.project_id,
        "environment_id": package.environment_id,
        "profile_id": package.profile_id,
        "source_module": package.source_module,
        "source_entity_type": package.source_entity_type,
        "source_entity_id": package.source_entity_id,
        "package_type": package.package_type,
        "status": package.status,
        "artifact_id": package.artifact_id,
        "manifest_id": package.manifest_id,
        "evidence_id": package.evidence_id,
        "approval_evidence_id": package.approval_evidence_id,
        "load_sequence": parse_json_list(package.load_sequence_json),
        "summary": parse_json_object(package.summary_json),
        "created_by": package.created_by,
        "registered_at": package.registered_at.isoformat() if package.registered_at else None,
    }


def existing_rates_package(db: Session, batch_id: str) -> LoadPlanPackage | None:
    return (
        db.query(LoadPlanPackage)
        .filter(LoadPlanPackage.source_module == "rates")
        .filter(LoadPlanPackage.source_entity_type == "rate_batch")
        .filter(LoadPlanPackage.source_entity_id == batch_id)
        .order_by(LoadPlanPackage.created_at.desc())
        .first()
    )


def latest_rates_export_evidence(db: Session, batch_id: str) -> Evidence | None:
    export_evidence = list_batch_export_evidence(db, batch_id)
    if not export_evidence:
        return None
    latest = export_evidence[0]
    if not latest.artifact_id or not latest.manifest_id:
        return None
    return latest


def load_sequence_for_batch(db: Session, batch_id: str) -> list[dict[str, object]]:
    tables = (
        db.query(RateBatchTable)
        .filter(RateBatchTable.batch_id == batch_id)
        .order_by(RateBatchTable.sequence_index)
        .all()
    )
    return [
        {
            "position": table.sequence_index,
            "table_name": table.table_name,
            "row_count": table.row_count,
            "requirement_level": table.requirement_level,
        }
        for table in tables
    ]


def register_rates_package(db: Session, *, batch: RateBatch, created_by: str) -> LoadPlanPackage:
    existing = existing_rates_package(db, batch.id)
    if existing:
        return existing
    if batch.status != "APPROVED":
        raise ValueError("Rate batch must be approved before Load Plan package intake.")

    export_evidence = latest_rates_export_evidence(db, batch.id)
    if export_evidence is None:
        raise ValueError("Rate batch must have a CSV export artifact before Load Plan package intake.")

    approval_evidence = get_existing_approval_evidence(db, batch.id)
    if approval_evidence is None:
        raise ValueError("Rate batch must have approval evidence before Load Plan package intake.")

    load_sequence = load_sequence_for_batch(db, batch.id)
    table_count = len(load_sequence)
    row_count = sum(int(item["row_count"]) for item in load_sequence)
    if table_count == 0 or row_count == 0:
        raise ValueError("Rate batch must have tables and rows before Load Plan package intake.")

    summary = {
        "source_module": "rates",
        "source_batch_id": batch.id,
        "scenario_code": batch.scenario_code,
        "domain_name": batch.domain_name,
        "source_status": batch.status,
        "package_type": "rates_csv_zip",
        "table_count": table_count,
        "row_count": row_count,
        "has_export_artifact": True,
        "has_approval_evidence": True,
    }
    package = LoadPlanPackage(
        project_id=batch.project_id,
        environment_id=batch.environment_id,
        profile_id=batch.profile_id,
        source_module="rates",
        source_entity_type="rate_batch",
        source_entity_id=batch.id,
        package_type="rates_csv_zip",
        status="REGISTERED",
        artifact_id=export_evidence.artifact_id,
        manifest_id=export_evidence.manifest_id,
        approval_evidence_id=approval_evidence.id,
        load_sequence_json=json.dumps(load_sequence, sort_keys=True),
        summary_json=json.dumps(summary, sort_keys=True),
        created_by=created_by,
        registered_at=utcnow(),
    )
    db.add(package)
    db.flush()

    evidence_summary = {
        "source_entity_type": "load_plan_package",
        "source_entity_id": package.id,
        "upstream_source_module": "rates",
        "upstream_entity_type": "rate_batch",
        "upstream_entity_id": batch.id,
        "package_type": "rates_csv_zip",
        "artifact_id": export_evidence.artifact_id,
        "manifest_id": export_evidence.manifest_id,
        "approval_evidence_id": approval_evidence.id,
        "table_count": table_count,
        "row_count": row_count,
    }
    intake_evidence = Evidence(
        project_id=batch.project_id,
        source_module="load_plan",
        evidence_type="load_plan_package_intake",
        summary_json=json.dumps(evidence_summary, sort_keys=True),
        artifact_id=export_evidence.artifact_id,
        manifest_id=export_evidence.manifest_id,
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db.add(intake_evidence)
    db.flush()

    package.evidence_id = intake_evidence.id
    db.add(
        AuditLog(
            actor_user_id=created_by,
            action="load_plan.package.register_from_rates",
            target_type="load_plan_package",
            target_id=package.id,
            metadata_json=json.dumps(
                {
                    "source_module": "rates",
                    "source_entity_id": batch.id,
                    "artifact_id": export_evidence.artifact_id,
                    "manifest_id": export_evidence.manifest_id,
                    "evidence_id": intake_evidence.id,
                },
                sort_keys=True,
            ),
        )
    )
    db.add(
        DomainEvent(
            event_type="load_plan.package.registered",
            source_module="load_plan",
            project_id=batch.project_id,
            aggregate_type="load_plan_package",
            aggregate_id=package.id,
            payload_json=json.dumps(
                {
                    "source_module": "rates",
                    "source_entity_id": batch.id,
                    "package_type": "rates_csv_zip",
                    "status": "REGISTERED",
                },
                sort_keys=True,
            ),
            status="PENDING",
        )
    )
    db.commit()
    db.refresh(package)
    return package
```

- [ ] **Step 5: Add routes and include router**

Create `src/otm_workbench/modules/load_plan/routes.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from otm_workbench.contracts import PageResponse
from otm_workbench.dependencies import get_db, require_user
from otm_workbench.models import LoadPlanPackage, RateBatch, User
from otm_workbench.modules.load_plan.packages import register_rates_package, serialize_load_plan_package

router = APIRouter(prefix="/api/v1/modules/load-plan", tags=["load-plan"])


@router.post("/packages/from-rates/{batch_id}")
def register_load_plan_package_from_rates(
    batch_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = db.query(RateBatch).filter(RateBatch.id == batch_id).first()
    if batch is None:
        raise HTTPException(status_code=404, detail="Rate batch not found.")
    try:
        package = register_rates_package(db, batch=batch, created_by=user.email)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize_load_plan_package(package)


@router.get("/packages")
def list_load_plan_packages(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    packages = db.query(LoadPlanPackage).order_by(LoadPlanPackage.created_at.desc()).all()
    items = [serialize_load_plan_package(package) for package in packages]
    return PageResponse(items=items, total=len(items))
```

Create `src/otm_workbench/modules/load_plan/__init__.py` if it was not already created:

```python
"""Load Plan module foundation."""
```

Modify `src/otm_workbench/main.py`:

```python
from otm_workbench.modules.load_plan.routes import router as load_plan_router
```

and inside `create_app()` after the Rates router include:

```python
app.include_router(load_plan_router)
```

- [ ] **Step 6: Run intake tests**

Run:

```bash
python -m pytest tests/test_load_plan_package_intake.py::test_register_rejects_unapproved_rate_batch tests/test_load_plan_package_intake.py::test_register_rejects_approved_rate_batch_without_export tests/test_load_plan_package_intake.py::test_register_rates_package_creates_load_plan_package -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

Run:

```bash
git add src/otm_workbench/modules/load_plan src/otm_workbench/main.py tests/test_load_plan_package_intake.py
git commit -m "feat: register rates load plan packages"
```

---

## Task 3: Detail, List, Summary, And Navigation

**Files:**
- Modify: `src/otm_workbench/modules/load_plan/packages.py`
- Modify: `src/otm_workbench/modules/load_plan/routes.py`
- Modify: `src/otm_workbench/platform/navigation.py`
- Test: `tests/test_load_plan_package_intake.py`

- [ ] **Step 1: Add failing list/detail/summary/navigation tests**

Append to `tests/test_load_plan_package_intake.py`:

```python
def test_load_plan_package_list_and_detail(client, admin_header):
    batch, export, approval = prepare_approved_exported_rate_batch(client, admin_header)
    created = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    ).json()

    listed = client.get("/api/v1/modules/load-plan/packages", headers=admin_header)
    detail = client.get(f"/api/v1/modules/load-plan/packages/{created['id']}", headers=admin_header)

    assert listed.status_code == 200
    assert detail.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == created["id"]
    assert detail.json()["artifact_id"] == export["artifact_id"]
    assert detail.json()["approval_evidence_id"] == approval["evidence_id"]
    assert detail.json()["summary"]["scenario_code"] == "ACCESSORIAL_ONLY"
    assert "OTM1.ACC_COST_001" not in json.dumps(detail.json())


def test_load_plan_summary_counts_packages(client, admin_header):
    batch, export, approval = prepare_approved_exported_rate_batch(client, admin_header)
    created = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    )
    assert created.status_code == 200

    response = client.get("/api/v1/modules/load-plan/summary", headers=admin_header)

    assert response.status_code == 200
    payload = response.json()
    assert payload["registered_packages"] == 1
    assert payload["by_source_module"] == {"rates": 1}
    assert payload["by_status"] == {"REGISTERED": 1}
    assert payload["next_actions"] == ["build_csvutil"]


def test_load_plan_module_is_registered(client, admin_header):
    modules = client.get("/api/v1/platform/modules", headers=admin_header)

    assert modules.status_code == 200
    module_ids = [item["id"] for item in modules.json()["items"]]
    assert "load_plan" in module_ids
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/test_load_plan_package_intake.py::test_load_plan_package_list_and_detail tests/test_load_plan_package_intake.py::test_load_plan_summary_counts_packages tests/test_load_plan_package_intake.py::test_load_plan_module_is_registered -q
```

Expected: FAIL because detail, summary, and module registration are missing.

- [ ] **Step 3: Add summary helper**

Append to `src/otm_workbench/modules/load_plan/packages.py`:

```python
def load_plan_package_summary(db: Session) -> dict[str, object]:
    packages = db.query(LoadPlanPackage).all()
    by_source_module: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for package in packages:
        by_source_module[package.source_module] = by_source_module.get(package.source_module, 0) + 1
        by_status[package.status] = by_status.get(package.status, 0) + 1
    return {
        "registered_packages": len(packages),
        "by_source_module": by_source_module,
        "by_status": by_status,
        "next_actions": ["build_csvutil"] if packages else [],
    }
```

- [ ] **Step 4: Add detail and summary routes**

Update `src/otm_workbench/modules/load_plan/routes.py` imports:

```python
from otm_workbench.modules.load_plan.packages import (
    load_plan_package_summary,
    register_rates_package,
    serialize_load_plan_package,
)
```

Append routes:

```python
@router.get("/packages/{package_id}")
def get_load_plan_package(
    package_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    package = db.query(LoadPlanPackage).filter(LoadPlanPackage.id == package_id).first()
    if package is None:
        raise HTTPException(status_code=404, detail="Load Plan package not found.")
    return serialize_load_plan_package(package)


@router.get("/summary")
def get_load_plan_summary(
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    return load_plan_package_summary(db)
```

- [ ] **Step 5: Register Load Plan module**

In `src/otm_workbench/platform/navigation.py`, add a module:

```python
Module(
    id="load_plan",
    display_name="Load Plan",
    route_base="/load-plan",
    status="PLANNED",
),
```

and update order:

```python
order = ["master_data", "home", "evidence", "rates", "load_plan", "admin", "dev_tools"]
```

- [ ] **Step 6: Run list/detail/summary/navigation tests**

Run:

```bash
python -m pytest tests/test_load_plan_package_intake.py::test_load_plan_package_list_and_detail tests/test_load_plan_package_intake.py::test_load_plan_summary_counts_packages tests/test_load_plan_package_intake.py::test_load_plan_module_is_registered -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

Run:

```bash
git add src/otm_workbench/modules/load_plan src/otm_workbench/platform/navigation.py tests/test_load_plan_package_intake.py
git commit -m "feat: expose load plan package intake APIs"
```

---

## Task 4: Idempotency And Client-Safe Metadata

**Files:**
- Modify: `src/otm_workbench/modules/load_plan/packages.py`
- Test: `tests/test_load_plan_package_intake.py`

- [ ] **Step 1: Add failing idempotency and evidence test**

Append to `tests/test_load_plan_package_intake.py`:

```python
def test_register_rates_package_creates_client_safe_evidence_audit_and_event(client, admin_header, db_session):
    batch, export, approval = prepare_approved_exported_rate_batch(client, admin_header)

    response = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    evidence = db_session.query(Evidence).filter(Evidence.id == payload["evidence_id"]).one()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "load_plan.package.register_from_rates").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "load_plan.package.registered").one()

    assert evidence.source_module == "load_plan"
    assert evidence.evidence_type == "load_plan_package_intake"
    assert evidence.client_safe is True
    assert evidence.artifact_id == export["artifact_id"]
    assert evidence.manifest_id == export["manifest_id"]
    assert approval["evidence_id"] in evidence.summary_json
    assert "OTM1.ACC_COST_001" not in evidence.summary_json
    assert audit.target_id == payload["id"]
    assert event.aggregate_id == payload["id"]
    assert event.status == "PENDING"


def test_register_rates_package_is_idempotent(client, admin_header, db_session):
    batch, export, approval = prepare_approved_exported_rate_batch(client, admin_header)

    first = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    )
    second = client.post(
        f"/api/v1/modules/load-plan/packages/from-rates/{batch['id']}",
        headers=admin_header,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["evidence_id"] == second.json()["evidence_id"]
    assert db_session.query(LoadPlanPackage).count() == 1
    assert db_session.query(Evidence).filter(Evidence.evidence_type == "load_plan_package_intake").count() == 1
    assert db_session.query(AuditLog).filter(AuditLog.action == "load_plan.package.register_from_rates").count() == 1
    assert db_session.query(DomainEvent).filter(DomainEvent.event_type == "load_plan.package.registered").count() == 1
```

- [ ] **Step 2: Run idempotency tests**

Run:

```bash
python -m pytest tests/test_load_plan_package_intake.py::test_register_rates_package_creates_client_safe_evidence_audit_and_event tests/test_load_plan_package_intake.py::test_register_rates_package_is_idempotent -q
```

Expected: PASS if Task 2 implemented idempotency and metadata correctly; FAIL if evidence/audit/event duplicates appear.

- [ ] **Step 3: Fix idempotency if needed**

If duplicate metadata appears, ensure `register_rates_package()` returns immediately before creating evidence/audit/event:

```python
existing = existing_rates_package(db, batch.id)
if existing:
    return existing
```

This must be the first branch in the function.

- [ ] **Step 4: Run full Load Plan intake tests**

Run:

```bash
python -m pytest tests/test_load_plan_package_intake.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add src/otm_workbench/modules/load_plan/packages.py tests/test_load_plan_package_intake.py
git commit -m "feat: make load plan package intake idempotent"
```

Skip the commit if no code changed after tests.

---

## Task 5: Documentation And Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README**

Add after the Rates approval paragraph:

```markdown
The Load Plan Package Intake slice registers approved Rates CSV exports as
backend-only Load Plan packages, preserving links to artifacts, manifests, and
client-safe evidence without generating CSVUTIL or cutover readiness outputs.
```

Update the verification command:

```powershell
python -m pytest tests/test_reference_catalog.py tests/test_rates_dictionary.py tests/test_rates_csv_preview.py tests/test_rates_batch_approval.py tests/test_load_plan_package_intake.py
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
rg -n "Synthetic|OTM1|PUBLIC|DEMO" README.md src tests docs/superpowers/specs/2026-05-18-load-plan-package-intake-design.md docs/superpowers/plans/2026-05-18-load-plan-package-intake.md
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
git commit -m "docs: document load plan package intake"
```

Skip if README was already committed in a prior task.

---

## Self-Review

Spec coverage:

- `LoadPlanPackage` persistence and migration: Task 1.
- Register approved Rates export as package: Task 2.
- Precondition rejects: Task 2.
- Package list/detail and summary: Task 3.
- Audit, event, and client-safe evidence: Task 4.
- Idempotency: Task 4.
- README, Alembic, tests, and Ruff: Task 5.

Scope guardrails:

- No CSVUTIL CTL/CL generation.
- No ZIP analysis.
- No setup review queue.
- No cutover readiness.
- No real OTM upload.
- No UI.
- No Data Factory intake.

The plan uses synthetic `OTM1` data only and never copies raw row values into Load Plan package or evidence summaries.
