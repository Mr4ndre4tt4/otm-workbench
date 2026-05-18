# Load Plan Setup Review Queue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add backend/API support for generating and listing client-safe Load Plan review items from ZIP Analysis findings.

**Architecture:** Add a `LoadPlanReviewItem` persistence model and migration, then implement a focused `modules/load_plan/review_queue.py` service that reads `LoadPlanZipAnalysis.findings_json`, creates idempotent `PENDING_REVIEW` items for `ERROR` and `WARNING` findings, and records audit/event metadata. Extend the existing Load Plan router with generate/list/detail endpoints while keeping review decisions and cutover readiness out of scope.

**Tech Stack:** Python, FastAPI, SQLAlchemy ORM, Alembic, pytest, stdlib `json`, existing Load Plan ZIP Analysis APIs.

---

## File Structure

- Create `migrations/versions/b9e6d1c4f8a2_load_plan_review_queue.py`: create/drop `load_plan_review_items`.
- Modify `src/otm_workbench/models.py`: add `LoadPlanReviewItem` near other Load Plan models.
- Create `src/otm_workbench/modules/load_plan/review_queue.py`: generation, mapping, serialization, idempotency.
- Modify `src/otm_workbench/modules/load_plan/routes.py`: add review queue endpoints and optional list filters.
- Create `tests/test_load_plan_review_queue.py`: TDD tests for persistence, generation, idempotency, API contracts, audit/event, data safety.
- Modify `README.md`: document backend-only Setup Review Queue slice.

No review decisions, status changes beyond initial `PENDING_REVIEW`, cutover readiness, OTM upload, CSVUTIL execution, or UI belong in this plan.

## Shared Test Helpers

Create local helpers in `tests/test_load_plan_review_queue.py`. Keep synthetic data only.

```python
import json
from pathlib import Path
import zipfile

from sqlalchemy import inspect

from otm_workbench.database import engine
from otm_workbench.models import Artifact


def create_rate_batch(client, admin_header, scenario_code="ACCESSORIAL_ONLY"):
    response = client.post(
        "/api/v1/modules/rates/batches",
        json={"scenario_code": scenario_code, "name": "Synthetic review queue batch", "domain_name": "OTM1"},
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
        json={"approval_note": "Reviewed for synthetic review queue package"},
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
    rewritten_path = artifact_path.with_suffix(".review-queue.zip")
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


def create_zip_analysis(client, admin_header, package):
    response = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": package["id"]},
        headers=admin_header,
    )
    assert response.status_code == 200
    return response.json()
```

## Task 1: Persistence Model And Migration

**Files:**
- Modify: `src/otm_workbench/models.py`
- Create: `migrations/versions/b9e6d1c4f8a2_load_plan_review_queue.py`
- Test: `tests/test_load_plan_review_queue.py`

- [ ] **Step 1: Write failing table existence test**

Create `tests/test_load_plan_review_queue.py` with the shared imports and helpers above, then add:

```python
def test_load_plan_review_items_table_exists_after_metadata_reset():
    tables = set(inspect(engine).get_table_names())

    assert "load_plan_review_items" in tables
```

- [ ] **Step 2: Run failing test**

Run:

```bash
python -m pytest tests/test_load_plan_review_queue.py::test_load_plan_review_items_table_exists_after_metadata_reset -q
```

Expected: FAIL because `load_plan_review_items` does not exist.

- [ ] **Step 3: Add ORM model**

In `src/otm_workbench/models.py`, add this class after `LoadPlanZipAnalysis`:

```python
class LoadPlanReviewItem(Base, TimestampMixin):
    __tablename__ = "load_plan_review_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    package_id: Mapped[str] = mapped_column(ForeignKey("load_plan_packages.id"), index=True)
    zip_analysis_id: Mapped[str] = mapped_column(ForeignKey("load_plan_zip_analyses.id"), index=True)
    source_type: Mapped[str] = mapped_column(String, default="zip_analysis_finding", index=True)
    source_code: Mapped[str] = mapped_column(String, index=True)
    severity: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, default="PENDING_REVIEW", index=True)
    category: Mapped[str] = mapped_column(String, index=True)
    table_name: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    file_name: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)
```

- [ ] **Step 4: Add Alembic migration**

Create `migrations/versions/b9e6d1c4f8a2_load_plan_review_queue.py`:

```python
"""load plan review queue

Revision ID: b9e6d1c4f8a2
Revises: a4c8e2f9b6d3
Create Date: 2026-05-18 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "b9e6d1c4f8a2"
down_revision: str | None = "a4c8e2f9b6d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "load_plan_review_items",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("environment_id", sa.String(), nullable=True),
        sa.Column("profile_id", sa.String(), nullable=True),
        sa.Column("package_id", sa.String(), nullable=False),
        sa.Column("zip_analysis_id", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("source_code", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("table_name", sa.String(), nullable=True),
        sa.Column("file_name", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["package_id"], ["load_plan_packages.id"]),
        sa.ForeignKeyConstraint(["zip_analysis_id"], ["load_plan_zip_analyses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in [
        "project_id",
        "environment_id",
        "profile_id",
        "package_id",
        "zip_analysis_id",
        "source_type",
        "source_code",
        "severity",
        "status",
        "category",
        "table_name",
    ]:
        op.create_index(
            f"ix_load_plan_review_items_{column}",
            "load_plan_review_items",
            [column],
        )


def downgrade() -> None:
    for column in [
        "table_name",
        "category",
        "status",
        "severity",
        "source_code",
        "source_type",
        "zip_analysis_id",
        "package_id",
        "profile_id",
        "environment_id",
        "project_id",
    ]:
        op.drop_index(f"ix_load_plan_review_items_{column}", table_name="load_plan_review_items")
    op.drop_table("load_plan_review_items")
```

- [ ] **Step 5: Run table test**

Run:

```bash
python -m pytest tests/test_load_plan_review_queue.py::test_load_plan_review_items_table_exists_after_metadata_reset -q
```

Expected: PASS.

- [ ] **Step 6: Commit persistence**

```bash
git add src/otm_workbench/models.py migrations/versions/b9e6d1c4f8a2_load_plan_review_queue.py tests/test_load_plan_review_queue.py
git commit -m "feat: add load plan review item model"
```

## Task 2: Review Queue Service And Generation API

**Files:**
- Create: `src/otm_workbench/modules/load_plan/review_queue.py`
- Modify: `src/otm_workbench/modules/load_plan/routes.py`
- Modify: `tests/test_load_plan_review_queue.py`

- [ ] **Step 1: Add failing no-findings generation test**

Append imports:

```python
from otm_workbench.models import AuditLog, DomainEvent, LoadPlanReviewItem
```

Append:

```python
def test_review_queue_generation_returns_zero_items_for_clean_zip_analysis(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    analysis = create_zip_analysis(client, admin_header, package)

    response = client.post(
        f"/api/v1/modules/load-plan/review-queue/from-zip-analysis/{analysis['id']}",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["analysis_id"] == analysis["id"]
    assert payload["package_id"] == package["id"]
    assert payload["created_count"] == 0
    assert payload["existing_count"] == 0
    assert payload["items"] == []
    assert db_session.query(LoadPlanReviewItem).count() == 0
```

- [ ] **Step 2: Run failing test**

Run:

```bash
python -m pytest tests/test_load_plan_review_queue.py::test_review_queue_generation_returns_zero_items_for_clean_zip_analysis -q
```

Expected: FAIL because review queue route/service does not exist.

- [ ] **Step 3: Implement review queue service**

Create `src/otm_workbench/modules/load_plan/review_queue.py`:

```python
import json

from sqlalchemy.orm import Session

from otm_workbench.models import AuditLog, DomainEvent, LoadPlanReviewItem, LoadPlanZipAnalysis
from otm_workbench.modules.load_plan.packages import parse_json_list, parse_json_object


SOURCE_TYPE = "zip_analysis_finding"
PENDING_STATUS = "PENDING_REVIEW"

CATEGORY_BY_CODE = {
    "ZIP_MANIFEST_MISSING": "PACKAGE",
    "ZIP_CSV_MISSING": "STRUCTURE",
    "CSV_TABLE_LINE_MISSING": "STRUCTURE",
    "CSV_HEADER_LINE_MISSING": "STRUCTURE",
    "CSV_TABLE_NOT_IN_LOAD_SEQUENCE": "SEQUENCE",
    "CSV_TABLE_NOT_IN_DATA_DICTIONARY": "DATA_DICTIONARY",
    "CSV_UNKNOWN_COLUMN": "DATA_DICTIONARY",
    "CSV_DATE_ALTER_SESSION_MISSING": "DATE_FORMAT",
    "CSV_ROW_COUNT_MISMATCH": "SEQUENCE",
}

TITLE_BY_CODE = {
    "ZIP_MANIFEST_MISSING": "ZIP manifest missing",
    "ZIP_CSV_MISSING": "ZIP CSV files missing",
    "CSV_TABLE_LINE_MISSING": "CSV table line missing",
    "CSV_HEADER_LINE_MISSING": "CSV header line missing",
    "CSV_TABLE_NOT_IN_LOAD_SEQUENCE": "CSV table outside load sequence",
    "CSV_TABLE_NOT_IN_DATA_DICTIONARY": "Unknown OTM Data Dictionary table",
    "CSV_UNKNOWN_COLUMN": "Unknown OTM Data Dictionary column",
    "CSV_DATE_ALTER_SESSION_MISSING": "Missing OTM date format directive",
    "CSV_ROW_COUNT_MISMATCH": "CSV row count differs from package sequence",
}

DESCRIPTION_BY_CODE = {
    "ZIP_MANIFEST_MISSING": "The package ZIP does not include manifest.json and needs review before load planning continues.",
    "ZIP_CSV_MISSING": "The package ZIP does not include CSV files under csv/ and needs review before load planning continues.",
    "CSV_TABLE_LINE_MISSING": "A CSV file is missing the expected table-name line and needs review before load planning continues.",
    "CSV_HEADER_LINE_MISSING": "A CSV file is missing the expected column-header line and needs review before load planning continues.",
    "CSV_TABLE_NOT_IN_LOAD_SEQUENCE": "A CSV table was not found in the package load sequence and needs review before load planning continues.",
    "CSV_TABLE_NOT_IN_DATA_DICTIONARY": "A CSV table was not found in the local OTM Data Dictionary and needs review before load planning continues.",
    "CSV_UNKNOWN_COLUMN": "A CSV column was not found in the local OTM Data Dictionary and needs review before load planning continues.",
    "CSV_DATE_ALTER_SESSION_MISSING": "A CSV includes DATE columns but does not declare the expected NLS date format before value lines.",
    "CSV_ROW_COUNT_MISMATCH": "A CSV row count differs from the package load sequence and needs review before load planning continues.",
}


def serialize_review_item(item: LoadPlanReviewItem) -> dict[str, object]:
    return {
        "id": item.id,
        "project_id": item.project_id,
        "environment_id": item.environment_id,
        "profile_id": item.profile_id,
        "package_id": item.package_id,
        "zip_analysis_id": item.zip_analysis_id,
        "source_type": item.source_type,
        "source_code": item.source_code,
        "severity": item.severity,
        "status": item.status,
        "category": item.category,
        "table_name": item.table_name,
        "file_name": item.file_name,
        "title": item.title,
        "description": item.description,
        "details": parse_json_object(item.details_json),
        "created_by": item.created_by,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


def review_item_identity(finding: dict[str, object]) -> tuple[str, str | None, str | None]:
    return (
        str(finding.get("code", "UNKNOWN_FINDING")),
        str(finding["table_name"]) if finding.get("table_name") is not None else None,
        str(finding["file_name"]) if finding.get("file_name") is not None else None,
    )


def existing_review_item(
    db: Session,
    *,
    analysis_id: str,
    source_code: str,
    table_name: str | None,
    file_name: str | None,
) -> LoadPlanReviewItem | None:
    query = (
        db.query(LoadPlanReviewItem)
        .filter(LoadPlanReviewItem.zip_analysis_id == analysis_id)
        .filter(LoadPlanReviewItem.source_type == SOURCE_TYPE)
        .filter(LoadPlanReviewItem.source_code == source_code)
    )
    query = query.filter(LoadPlanReviewItem.table_name.is_(None) if table_name is None else LoadPlanReviewItem.table_name == table_name)
    query = query.filter(LoadPlanReviewItem.file_name.is_(None) if file_name is None else LoadPlanReviewItem.file_name == file_name)
    return query.first()


def build_review_item(
    *,
    analysis: LoadPlanZipAnalysis,
    finding: dict[str, object],
    created_by: str,
) -> LoadPlanReviewItem:
    source_code, table_name, file_name = review_item_identity(finding)
    category = CATEGORY_BY_CODE.get(source_code, "PACKAGE")
    title = TITLE_BY_CODE.get(source_code, "Package finding requires review")
    description = DESCRIPTION_BY_CODE.get(
        source_code,
        "A local package analysis finding needs review before load planning continues.",
    )
    severity = str(finding.get("severity", "WARNING"))
    details = finding.get("details", {})
    details_json = json.dumps(details if isinstance(details, dict) else {}, sort_keys=True)
    return LoadPlanReviewItem(
        project_id=analysis.project_id,
        environment_id=analysis.environment_id,
        profile_id=analysis.profile_id,
        package_id=analysis.package_id,
        zip_analysis_id=analysis.id,
        source_type=SOURCE_TYPE,
        source_code=source_code,
        severity=severity,
        status=PENDING_STATUS,
        category=category,
        table_name=table_name,
        file_name=file_name,
        title=title,
        description=description,
        details_json=details_json,
        created_by=created_by,
    )


def generate_review_queue_from_zip_analysis(
    db: Session,
    *,
    analysis: LoadPlanZipAnalysis,
    generated_by: str,
) -> dict[str, object]:
    if analysis.status != "ANALYZED":
        raise ValueError("ZIP Analysis must be ANALYZED before review queue generation.")
    findings = parse_json_list(analysis.findings_json)
    selected = [item for item in findings if item.get("severity") in {"ERROR", "WARNING"}]
    created: list[LoadPlanReviewItem] = []
    existing: list[LoadPlanReviewItem] = []

    for finding in selected:
        source_code, table_name, file_name = review_item_identity(finding)
        current = existing_review_item(
            db,
            analysis_id=analysis.id,
            source_code=source_code,
            table_name=table_name,
            file_name=file_name,
        )
        if current is not None:
            existing.append(current)
            continue
        item = build_review_item(analysis=analysis, finding=finding, created_by=generated_by)
        db.add(item)
        db.flush()
        created.append(item)

    db.add(
        AuditLog(
            actor_user_id=generated_by,
            action="load_plan.review_queue.generate_from_zip_analysis",
            target_type="load_plan_zip_analysis",
            target_id=analysis.id,
            metadata_json=json.dumps(
                {
                    "package_id": analysis.package_id,
                    "created_count": len(created),
                    "existing_count": len(existing),
                    "selected_finding_count": len(selected),
                },
                sort_keys=True,
            ),
        )
    )
    db.add(
        DomainEvent(
            event_type="load_plan.review_queue.generated",
            source_module="load_plan",
            project_id=analysis.project_id,
            aggregate_type="load_plan_zip_analysis",
            aggregate_id=analysis.id,
            payload_json=json.dumps(
                {
                    "package_id": analysis.package_id,
                    "created_count": len(created),
                    "existing_count": len(existing),
                },
                sort_keys=True,
            ),
            status="PENDING",
        )
    )
    db.commit()
    for item in created + existing:
        db.refresh(item)
    return {
        "analysis_id": analysis.id,
        "package_id": analysis.package_id,
        "created_count": len(created),
        "existing_count": len(existing),
        "items": [serialize_review_item(item) for item in created + existing],
    }
```

- [ ] **Step 4: Add route import and generation endpoint**

In `src/otm_workbench/modules/load_plan/routes.py`, update imports:

```python
from otm_workbench.models import CsvutilBuild, LoadPlanPackage, LoadPlanReviewItem, LoadPlanZipAnalysis, RateBatch, User
from otm_workbench.modules.load_plan.review_queue import (
    generate_review_queue_from_zip_analysis,
    serialize_review_item,
)
```

Add endpoint after ZIP Analysis endpoints:

```python
@router.post("/review-queue/from-zip-analysis/{analysis_id}")
def generate_review_queue_from_analysis(
    analysis_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    analysis = db.query(LoadPlanZipAnalysis).filter(LoadPlanZipAnalysis.id == analysis_id).first()
    if analysis is None:
        raise HTTPException(status_code=404, detail="ZIP analysis not found.")
    try:
        return generate_review_queue_from_zip_analysis(
            db,
            analysis=analysis,
            generated_by=user.email,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
```

- [ ] **Step 5: Run no-findings generation test**

Run:

```bash
python -m pytest tests/test_load_plan_review_queue.py::test_review_queue_generation_returns_zero_items_for_clean_zip_analysis -q
```

Expected: PASS.

- [ ] **Step 6: Commit service and generation endpoint**

```bash
git add src/otm_workbench/modules/load_plan/review_queue.py src/otm_workbench/modules/load_plan/routes.py tests/test_load_plan_review_queue.py
git commit -m "feat: generate load plan review queue"
```

## Task 3: Findings, Idempotency, And Audit/Event

**Files:**
- Modify: `tests/test_load_plan_review_queue.py`
- Modify: `src/otm_workbench/modules/load_plan/review_queue.py`

- [ ] **Step 1: Add unknown-column item test**

Append:

```python
def test_review_queue_generation_creates_item_for_unknown_column(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    rewrite_export_with_unknown_column(db_session, export)
    analysis = create_zip_analysis(client, admin_header, package)

    response = client.post(
        f"/api/v1/modules/load-plan/review-queue/from-zip-analysis/{analysis['id']}",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["created_count"] == 1
    assert payload["existing_count"] == 0
    item = payload["items"][0]
    assert item["source_type"] == "zip_analysis_finding"
    assert item["source_code"] == "CSV_UNKNOWN_COLUMN"
    assert item["severity"] == "ERROR"
    assert item["status"] == "PENDING_REVIEW"
    assert item["category"] == "DATA_DICTIONARY"
    assert item["table_name"] == "ACCESSORIAL_COST"
    assert item["file_name"] == "csv/001_ACCESSORIAL_COST.csv"
    assert item["title"] == "Unknown OTM Data Dictionary column"
    assert item["details"] == {"column_name": "SYNTHETIC_UNKNOWN_COLUMN"}
    assert "DEMO" not in json.dumps(payload)
    assert "OTM1.ACC_COST_001" not in json.dumps(payload)
    assert db_session.query(LoadPlanReviewItem).count() == 1
```

- [ ] **Step 2: Add idempotency test**

Append:

```python
def test_review_queue_generation_is_idempotent_for_same_analysis(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    rewrite_export_with_unknown_column(db_session, export)
    analysis = create_zip_analysis(client, admin_header, package)

    first = client.post(
        f"/api/v1/modules/load-plan/review-queue/from-zip-analysis/{analysis['id']}",
        headers=admin_header,
    )
    second = client.post(
        f"/api/v1/modules/load-plan/review-queue/from-zip-analysis/{analysis['id']}",
        headers=admin_header,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["created_count"] == 1
    assert second.json()["created_count"] == 0
    assert second.json()["existing_count"] == 1
    assert first.json()["items"][0]["id"] == second.json()["items"][0]["id"]
    assert db_session.query(LoadPlanReviewItem).count() == 1
```

- [ ] **Step 3: Add audit/event data-safety test**

Append:

```python
def test_review_queue_generation_creates_audit_and_event(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    rewrite_export_with_unknown_column(db_session, export)
    analysis = create_zip_analysis(client, admin_header, package)

    response = client.post(
        f"/api/v1/modules/load-plan/review-queue/from-zip-analysis/{analysis['id']}",
        headers=admin_header,
    )

    assert response.status_code == 200
    audit = db_session.query(AuditLog).filter(AuditLog.action == "load_plan.review_queue.generate_from_zip_analysis").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "load_plan.review_queue.generated").one()
    assert audit.target_id == analysis["id"]
    assert event.aggregate_id == analysis["id"]
    assert event.status == "PENDING"
    assert "OTM1.ACC_COST_001" not in audit.metadata_json
    assert "OTM1.ACC_COST_001" not in event.payload_json
    assert "DEMO" not in audit.metadata_json
    assert "DEMO" not in event.payload_json
```

- [ ] **Step 4: Run findings/idempotency/audit tests**

Run:

```bash
python -m pytest tests/test_load_plan_review_queue.py::test_review_queue_generation_creates_item_for_unknown_column tests/test_load_plan_review_queue.py::test_review_queue_generation_is_idempotent_for_same_analysis tests/test_load_plan_review_queue.py::test_review_queue_generation_creates_audit_and_event -q
```

Expected: PASS.

- [ ] **Step 5: Commit findings/idempotency**

```bash
git add src/otm_workbench/modules/load_plan/review_queue.py tests/test_load_plan_review_queue.py
git commit -m "test: cover review queue generation"
```

## Task 4: List, Detail, Filters, And Errors

**Files:**
- Modify: `src/otm_workbench/modules/load_plan/routes.py`
- Modify: `tests/test_load_plan_review_queue.py`

- [ ] **Step 1: Add list/detail/filter tests**

Append:

```python
def test_review_queue_list_detail_and_filters(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    rewrite_export_with_unknown_column(db_session, export)
    analysis = create_zip_analysis(client, admin_header, package)
    created = client.post(
        f"/api/v1/modules/load-plan/review-queue/from-zip-analysis/{analysis['id']}",
        headers=admin_header,
    ).json()["items"][0]

    listed = client.get("/api/v1/modules/load-plan/review-queue", headers=admin_header)
    filtered = client.get(
        "/api/v1/modules/load-plan/review-queue",
        params={"status": "PENDING_REVIEW", "severity": "ERROR", "package_id": package["id"]},
        headers=admin_header,
    )
    detail = client.get(f"/api/v1/modules/load-plan/review-queue/{created['id']}", headers=admin_header)

    assert listed.status_code == 200
    assert filtered.status_code == 200
    assert detail.status_code == 200
    assert listed.json()["total"] == 1
    assert filtered.json()["total"] == 1
    assert filtered.json()["items"][0]["id"] == created["id"]
    assert detail.json()["details"] == {"column_name": "SYNTHETIC_UNKNOWN_COLUMN"}
```

- [ ] **Step 2: Add missing analysis and detail 404 tests**

Append:

```python
def test_review_queue_generation_rejects_missing_analysis(client, admin_header):
    response = client.post(
        "/api/v1/modules/load-plan/review-queue/from-zip-analysis/missing_analysis",
        headers=admin_header,
    )

    assert response.status_code == 404


def test_review_queue_detail_rejects_missing_item(client, admin_header):
    response = client.get("/api/v1/modules/load-plan/review-queue/missing_item", headers=admin_header)

    assert response.status_code == 404
```

- [ ] **Step 3: Add list/detail routes**

Add these endpoints after the generation endpoint in `src/otm_workbench/modules/load_plan/routes.py`:

```python
@router.get("/review-queue")
def list_review_queue_items(
    status: str | None = None,
    severity: str | None = None,
    package_id: str | None = None,
    zip_analysis_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    query = db.query(LoadPlanReviewItem)
    if status:
        query = query.filter(LoadPlanReviewItem.status == status)
    if severity:
        query = query.filter(LoadPlanReviewItem.severity == severity)
    if package_id:
        query = query.filter(LoadPlanReviewItem.package_id == package_id)
    if zip_analysis_id:
        query = query.filter(LoadPlanReviewItem.zip_analysis_id == zip_analysis_id)
    items = query.order_by(LoadPlanReviewItem.created_at.desc()).all()
    return PageResponse(items=[serialize_review_item(item) for item in items], total=len(items))


@router.get("/review-queue/{item_id}")
def get_review_queue_item(
    item_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    item = db.query(LoadPlanReviewItem).filter(LoadPlanReviewItem.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Review queue item not found.")
    return serialize_review_item(item)
```

- [ ] **Step 4: Run list/detail/error tests**

Run:

```bash
python -m pytest tests/test_load_plan_review_queue.py::test_review_queue_list_detail_and_filters tests/test_load_plan_review_queue.py::test_review_queue_generation_rejects_missing_analysis tests/test_load_plan_review_queue.py::test_review_queue_detail_rejects_missing_item -q
```

Expected: PASS.

- [ ] **Step 5: Commit routes**

```bash
git add src/otm_workbench/modules/load_plan/routes.py tests/test_load_plan_review_queue.py
git commit -m "feat: expose load plan review queue"
```

## Task 5: README And Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README**

Add after the Load Plan ZIP Analysis paragraph:

```markdown
The Load Plan Setup Review Queue slice creates client-safe `PENDING_REVIEW`
items from ZIP Analysis findings, preserving audit/event metadata, without
making review decisions, approving packages, or producing cutover readiness.
```

Update the focused verification command to include:

```powershell
tests/test_load_plan_review_queue.py
```

- [ ] **Step 2: Run focused tests**

Run:

```bash
python -m pytest tests/test_load_plan_review_queue.py -q
```

Expected: all Review Queue tests PASS.

- [ ] **Step 3: Run full verification**

Run:

```bash
python -m pytest -q
python -m alembic upgrade head
python -m ruff check src tests
```

Expected:

- pytest passes all tests.
- Alembic upgrades through `b9e6d1c4f8a2`.
- Ruff reports no issues.

- [ ] **Step 4: Commit docs**

```bash
git add README.md
git commit -m "docs: document load plan review queue"
```

## Final Acceptance Checklist

- [ ] `load_plan_review_items` exists after metadata reset.
- [ ] Generation from a clean ZIP Analysis returns zero items.
- [ ] Generation from `CSV_UNKNOWN_COLUMN` creates one `PENDING_REVIEW` item.
- [ ] Generated items include source code, severity, status, category, table, file, title, description, and parsed details.
- [ ] Generation is idempotent for the same analysis/finding.
- [ ] Audit log and domain event are created for generation.
- [ ] List endpoint supports exact-match filters.
- [ ] Detail endpoint returns one serialized item.
- [ ] Missing analysis and missing item return 404.
- [ ] Raw row values such as `OTM1.ACC_COST_001` and synthetic value `DEMO` are not persisted in review item payloads, audit metadata, or events.
- [ ] No review decisions, status transition endpoint, cutover readiness, OTM upload, CSVUTIL execution, or UI was added.
