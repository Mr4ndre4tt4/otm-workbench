# Load Plan Review Decisions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add backend/API support for deciding Load Plan review queue items with append-only decision history and client-safe evidence.

**Architecture:** Add a `LoadPlanReviewDecision` persistence model and migration, then extend `modules/load_plan/review_queue.py` with decision validation, decision persistence, review-item status updates, evidence, audit, event, and serializers. Extend the existing Load Plan router with `POST /review-queue/{item_id}/decide` and enrich list/detail review queue responses with latest decision metadata.

**Tech Stack:** Python, FastAPI, Pydantic, SQLAlchemy ORM, Alembic, pytest, stdlib `json`, existing Load Plan Review Queue APIs.

---

## File Structure

- Create `migrations/versions/c7d2f4a9e1b5_load_plan_review_decisions.py`: create/drop `load_plan_review_decisions`.
- Modify `src/otm_workbench/models.py`: add `LoadPlanReviewDecision`.
- Modify `src/otm_workbench/modules/load_plan/review_queue.py`: add allowed statuses, decision serializer, latest-decision lookup, decide service, and enriched review item serialization.
- Modify `src/otm_workbench/modules/load_plan/routes.py`: add request model and decide endpoint; pass DB session to review item serializers for latest decision metadata.
- Create `tests/test_load_plan_review_decisions.py`: TDD tests for table, decision flow, list/detail metadata, invalid status, missing item, re-decision, and data safety.
- Modify `README.md`: document backend-only Review Decisions slice.

No cutover readiness, readiness blockers/checklists, package status changes, OTM upload, CSVUTIL execution, external Oracle calls, or UI belong in this plan.

## Shared Test Helpers

Create local helpers in `tests/test_load_plan_review_decisions.py`. Keep all examples synthetic.

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
    LoadPlanReviewDecision,
    LoadPlanReviewItem,
)


def create_rate_batch(client, admin_header, scenario_code="ACCESSORIAL_ONLY"):
    response = client.post(
        "/api/v1/modules/rates/batches",
        json={"scenario_code": scenario_code, "name": "Synthetic review decision batch", "domain_name": "OTM1"},
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
        json={"approval_note": "Reviewed for synthetic review decision package"},
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
    rewritten_path = artifact_path.with_suffix(".review-decisions.zip")
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


def create_review_item(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    rewrite_export_with_unknown_column(db_session, export)
    analysis = client.post(
        "/api/v1/modules/load-plan/zip-analysis",
        json={"package_id": package["id"]},
        headers=admin_header,
    )
    assert analysis.status_code == 200
    review = client.post(
        f"/api/v1/modules/load-plan/review-queue/from-zip-analysis/{analysis.json()['id']}",
        headers=admin_header,
    )
    assert review.status_code == 200
    return package, analysis.json(), review.json()["items"][0]
```

## Task 1: Persistence Model And Migration

**Files:**
- Modify: `src/otm_workbench/models.py`
- Create: `migrations/versions/c7d2f4a9e1b5_load_plan_review_decisions.py`
- Test: `tests/test_load_plan_review_decisions.py`

- [ ] **Step 1: Write failing table existence test**

Create `tests/test_load_plan_review_decisions.py` with the shared imports and helpers above, then add:

```python
def test_load_plan_review_decisions_table_exists_after_metadata_reset():
    tables = set(inspect(engine).get_table_names())

    assert "load_plan_review_decisions" in tables
```

- [ ] **Step 2: Run failing test**

Run:

```bash
python -m pytest tests/test_load_plan_review_decisions.py::test_load_plan_review_decisions_table_exists_after_metadata_reset -q
```

Expected: FAIL because `load_plan_review_decisions` does not exist.

- [ ] **Step 3: Add ORM model**

In `src/otm_workbench/models.py`, add this class after `LoadPlanReviewItem`:

```python
class LoadPlanReviewDecision(Base, TimestampMixin):
    __tablename__ = "load_plan_review_decisions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    package_id: Mapped[str] = mapped_column(ForeignKey("load_plan_packages.id"), index=True)
    review_item_id: Mapped[str] = mapped_column(ForeignKey("load_plan_review_items.id"), index=True)
    decision_status: Mapped[str] = mapped_column(String, index=True)
    decision_note: Mapped[str] = mapped_column(Text, default="")
    evidence_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    decided_by: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    decided_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
```

- [ ] **Step 4: Add Alembic migration**

Create `migrations/versions/c7d2f4a9e1b5_load_plan_review_decisions.py`:

```python
"""load plan review decisions

Revision ID: c7d2f4a9e1b5
Revises: b9e6d1c4f8a2
Create Date: 2026-05-18 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c7d2f4a9e1b5"
down_revision: str | None = "b9e6d1c4f8a2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "load_plan_review_decisions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("environment_id", sa.String(), nullable=True),
        sa.Column("profile_id", sa.String(), nullable=True),
        sa.Column("package_id", sa.String(), nullable=False),
        sa.Column("review_item_id", sa.String(), nullable=False),
        sa.Column("decision_status", sa.String(), nullable=False),
        sa.Column("decision_note", sa.Text(), nullable=False),
        sa.Column("evidence_id", sa.String(), nullable=True),
        sa.Column("decided_by", sa.String(), nullable=True),
        sa.Column("decided_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["package_id"], ["load_plan_packages.id"]),
        sa.ForeignKeyConstraint(["review_item_id"], ["load_plan_review_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in [
        "project_id",
        "environment_id",
        "profile_id",
        "package_id",
        "review_item_id",
        "decision_status",
        "evidence_id",
        "decided_by",
    ]:
        op.create_index(
            f"ix_load_plan_review_decisions_{column}",
            "load_plan_review_decisions",
            [column],
        )


def downgrade() -> None:
    for column in [
        "decided_by",
        "evidence_id",
        "decision_status",
        "review_item_id",
        "package_id",
        "profile_id",
        "environment_id",
        "project_id",
    ]:
        op.drop_index(f"ix_load_plan_review_decisions_{column}", table_name="load_plan_review_decisions")
    op.drop_table("load_plan_review_decisions")
```

- [ ] **Step 5: Run table test**

Run:

```bash
python -m pytest tests/test_load_plan_review_decisions.py::test_load_plan_review_decisions_table_exists_after_metadata_reset -q
```

Expected: PASS.

- [ ] **Step 6: Commit persistence**

```bash
git add src/otm_workbench/models.py migrations/versions/c7d2f4a9e1b5_load_plan_review_decisions.py tests/test_load_plan_review_decisions.py
git commit -m "feat: add load plan review decision model"
```

## Task 2: Decision Service And Endpoint

**Files:**
- Modify: `src/otm_workbench/modules/load_plan/review_queue.py`
- Modify: `src/otm_workbench/modules/load_plan/routes.py`
- Modify: `tests/test_load_plan_review_decisions.py`

- [ ] **Step 1: Add failing decision flow test**

Append:

```python
def test_review_decision_updates_item_and_creates_evidence_audit_event(client, admin_header, db_session):
    package, analysis, item = create_review_item(client, admin_header, db_session)

    response = client.post(
        f"/api/v1/modules/load-plan/review-queue/{item['id']}/decide",
        json={"decision_status": "NEEDS_MANUAL_ACTION", "decision_note": "Synthetic reviewer note"},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    decision = db_session.query(LoadPlanReviewDecision).filter(LoadPlanReviewDecision.id == payload["id"]).one()
    refreshed_item = db_session.query(LoadPlanReviewItem).filter(LoadPlanReviewItem.id == item["id"]).one()
    evidence = db_session.query(Evidence).filter(Evidence.id == payload["evidence_id"]).one()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "load_plan.review_queue.decide").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "load_plan.review_queue.decided").one()

    assert payload["review_item_id"] == item["id"]
    assert payload["package_id"] == package["id"]
    assert payload["decision_status"] == "NEEDS_MANUAL_ACTION"
    assert payload["decision_note"] == "Synthetic reviewer note"
    assert payload["decided_by"] == "admin@example.com"
    assert payload["review_item"]["status"] == "NEEDS_MANUAL_ACTION"
    assert payload["review_item"]["latest_decision_id"] == payload["id"]
    assert decision.decision_note == "Synthetic reviewer note"
    assert refreshed_item.status == "NEEDS_MANUAL_ACTION"
    assert evidence.evidence_type == "load_plan_review_decision"
    assert evidence.client_safe is True
    assert audit.target_id == payload["id"]
    assert event.aggregate_id == payload["id"]
    assert "Synthetic reviewer note" not in audit.metadata_json
    assert "Synthetic reviewer note" not in event.payload_json
    assert "OTM1.ACC_COST_001" not in audit.metadata_json
    assert "OTM1.ACC_COST_001" not in event.payload_json
```

- [ ] **Step 2: Run failing decision flow test**

Run:

```bash
python -m pytest tests/test_load_plan_review_decisions.py::test_review_decision_updates_item_and_creates_evidence_audit_event -q
```

Expected: FAIL because decision endpoint/service does not exist.

- [ ] **Step 3: Extend review queue service**

In `src/otm_workbench/modules/load_plan/review_queue.py`, update imports:

```python
from otm_workbench.models import (
    AuditLog,
    DomainEvent,
    Evidence,
    LoadPlanReviewDecision,
    LoadPlanReviewItem,
    LoadPlanZipAnalysis,
    utcnow,
)
```

Add constants:

```python
ALLOWED_DECISION_STATUSES = {
    "CONFIRMED",
    "REJECTED",
    "NEEDS_MANUAL_ACTION",
    "EXCLUDED_FROM_CUTOVER",
}
```

Add functions after `generate_review_queue_from_zip_analysis`:

```python
def latest_review_decision(db: Session, item_id: str) -> LoadPlanReviewDecision | None:
    return (
        db.query(LoadPlanReviewDecision)
        .filter(LoadPlanReviewDecision.review_item_id == item_id)
        .order_by(LoadPlanReviewDecision.decided_at.desc(), LoadPlanReviewDecision.created_at.desc())
        .first()
    )


def serialize_review_item_with_latest_decision(db: Session, item: LoadPlanReviewItem) -> dict[str, object]:
    payload = serialize_review_item(item)
    decision = latest_review_decision(db, item.id)
    payload["latest_decision_id"] = decision.id if decision else None
    payload["latest_decision_status"] = decision.decision_status if decision else None
    payload["latest_decided_at"] = decision.decided_at.isoformat() if decision and decision.decided_at else None
    return payload


def serialize_review_decision(db: Session, decision: LoadPlanReviewDecision) -> dict[str, object]:
    item = db.query(LoadPlanReviewItem).filter(LoadPlanReviewItem.id == decision.review_item_id).one()
    return {
        "id": decision.id,
        "project_id": decision.project_id,
        "environment_id": decision.environment_id,
        "profile_id": decision.profile_id,
        "package_id": decision.package_id,
        "review_item_id": decision.review_item_id,
        "decision_status": decision.decision_status,
        "decision_note": decision.decision_note,
        "evidence_id": decision.evidence_id,
        "decided_by": decision.decided_by,
        "decided_at": decision.decided_at.isoformat() if decision.decided_at else None,
        "review_item": serialize_review_item_with_latest_decision(db, item),
    }


def decide_review_item(
    db: Session,
    *,
    item: LoadPlanReviewItem,
    decision_status: str,
    decision_note: str,
    decided_by: str,
) -> LoadPlanReviewDecision:
    if decision_status not in ALLOWED_DECISION_STATUSES:
        raise ValueError("Invalid review decision status.")
    note = decision_note.strip()
    decided_at = utcnow()
    decision = LoadPlanReviewDecision(
        project_id=item.project_id,
        environment_id=item.environment_id,
        profile_id=item.profile_id,
        package_id=item.package_id,
        review_item_id=item.id,
        decision_status=decision_status,
        decision_note=note,
        decided_by=decided_by,
        decided_at=decided_at,
    )
    db.add(decision)
    db.flush()

    evidence_summary = {
        "source_entity_type": "load_plan_review_decision",
        "source_entity_id": decision.id,
        "review_item_id": item.id,
        "package_id": item.package_id,
        "decision_status": decision_status,
        "decision_note_present": bool(note),
        "decided_by": decided_by,
        "decided_at": decided_at.isoformat(),
    }
    evidence = Evidence(
        project_id=item.project_id,
        source_module="load_plan",
        evidence_type="load_plan_review_decision",
        summary_json=json.dumps(evidence_summary, sort_keys=True),
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db.add(evidence)
    db.flush()

    decision.evidence_id = evidence.id
    item.status = decision_status
    db.add(
        AuditLog(
            actor_user_id=decided_by,
            action="load_plan.review_queue.decide",
            target_type="load_plan_review_decision",
            target_id=decision.id,
            metadata_json=json.dumps(
                {
                    "package_id": item.package_id,
                    "review_item_id": item.id,
                    "decision_status": decision_status,
                    "evidence_id": evidence.id,
                },
                sort_keys=True,
            ),
        )
    )
    db.add(
        DomainEvent(
            event_type="load_plan.review_queue.decided",
            source_module="load_plan",
            project_id=item.project_id,
            aggregate_type="load_plan_review_decision",
            aggregate_id=decision.id,
            payload_json=json.dumps(
                {
                    "package_id": item.package_id,
                    "review_item_id": item.id,
                    "decision_status": decision_status,
                },
                sort_keys=True,
            ),
            status="PENDING",
        )
    )
    db.commit()
    db.refresh(decision)
    return decision
```

- [ ] **Step 4: Add route request model and endpoint**

In `src/otm_workbench/modules/load_plan/routes.py`, update imports:

```python
from otm_workbench.modules.load_plan.review_queue import (
    decide_review_item,
    generate_review_queue_from_zip_analysis,
    serialize_review_decision,
    serialize_review_item,
    serialize_review_item_with_latest_decision,
)
```

Add request model near other request models:

```python
class ReviewDecisionRequest(BaseModel):
    decision_status: str
    decision_note: str = ""
```

Add endpoint after review queue detail endpoint:

```python
@router.post("/review-queue/{item_id}/decide")
def decide_review_queue_item(
    item_id: str,
    payload: ReviewDecisionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    item = db.query(LoadPlanReviewItem).filter(LoadPlanReviewItem.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Review queue item not found.")
    try:
        decision = decide_review_item(
            db,
            item=item,
            decision_status=payload.decision_status,
            decision_note=payload.decision_note,
            decided_by=user.email,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize_review_decision(db, decision)
```

- [ ] **Step 5: Run decision flow test**

Run:

```bash
python -m pytest tests/test_load_plan_review_decisions.py::test_review_decision_updates_item_and_creates_evidence_audit_event -q
```

Expected: PASS.

- [ ] **Step 6: Commit decision endpoint**

```bash
git add src/otm_workbench/modules/load_plan/review_queue.py src/otm_workbench/modules/load_plan/routes.py tests/test_load_plan_review_decisions.py
git commit -m "feat: decide load plan review items"
```

## Task 3: Latest Decision In Review Queue List And Detail

**Files:**
- Modify: `src/otm_workbench/modules/load_plan/routes.py`
- Modify: `tests/test_load_plan_review_decisions.py`

- [ ] **Step 1: Add latest metadata tests**

Append:

```python
def test_review_queue_list_and_detail_include_latest_decision(client, admin_header, db_session):
    package, analysis, item = create_review_item(client, admin_header, db_session)
    decision = client.post(
        f"/api/v1/modules/load-plan/review-queue/{item['id']}/decide",
        json={"decision_status": "CONFIRMED", "decision_note": "Synthetic confirmation note"},
        headers=admin_header,
    ).json()

    listed = client.get("/api/v1/modules/load-plan/review-queue", headers=admin_header)
    detail = client.get(f"/api/v1/modules/load-plan/review-queue/{item['id']}", headers=admin_header)

    assert listed.status_code == 200
    assert detail.status_code == 200
    listed_item = listed.json()["items"][0]
    detail_item = detail.json()
    assert listed_item["latest_decision_id"] == decision["id"]
    assert listed_item["latest_decision_status"] == "CONFIRMED"
    assert listed_item["latest_decided_at"]
    assert detail_item["latest_decision_id"] == decision["id"]
    assert detail_item["latest_decision_status"] == "CONFIRMED"
    assert detail_item["latest_decided_at"]
```

- [ ] **Step 2: Run failing latest metadata test**

Run:

```bash
python -m pytest tests/test_load_plan_review_decisions.py::test_review_queue_list_and_detail_include_latest_decision -q
```

Expected: FAIL until list/detail routes use `serialize_review_item_with_latest_decision`.

- [ ] **Step 3: Update review queue list/detail serializers**

In `src/otm_workbench/modules/load_plan/routes.py`, update list return:

```python
return PageResponse(
    items=[serialize_review_item_with_latest_decision(db, item) for item in items],
    total=len(items),
)
```

Update detail return:

```python
return serialize_review_item_with_latest_decision(db, item)
```

- [ ] **Step 4: Run latest metadata test**

Run:

```bash
python -m pytest tests/test_load_plan_review_decisions.py::test_review_queue_list_and_detail_include_latest_decision -q
```

Expected: PASS.

- [ ] **Step 5: Commit latest metadata**

```bash
git add src/otm_workbench/modules/load_plan/routes.py tests/test_load_plan_review_decisions.py
git commit -m "feat: expose latest review decision metadata"
```

## Task 4: Errors And Re-Decisions

**Files:**
- Modify: `tests/test_load_plan_review_decisions.py`
- Modify: `src/otm_workbench/modules/load_plan/review_queue.py`

- [ ] **Step 1: Add invalid and missing item tests**

Append:

```python
def test_review_decision_rejects_invalid_status_without_changing_item(client, admin_header, db_session):
    package, analysis, item = create_review_item(client, admin_header, db_session)

    response = client.post(
        f"/api/v1/modules/load-plan/review-queue/{item['id']}/decide",
        json={"decision_status": "READY_FOR_CUTOVER", "decision_note": "Synthetic invalid note"},
        headers=admin_header,
    )

    refreshed_item = db_session.query(LoadPlanReviewItem).filter(LoadPlanReviewItem.id == item["id"]).one()
    assert response.status_code == 400
    assert refreshed_item.status == "PENDING_REVIEW"
    assert db_session.query(LoadPlanReviewDecision).count() == 0


def test_review_decision_rejects_missing_item(client, admin_header):
    response = client.post(
        "/api/v1/modules/load-plan/review-queue/missing_item/decide",
        json={"decision_status": "CONFIRMED", "decision_note": "Synthetic note"},
        headers=admin_header,
    )

    assert response.status_code == 404
```

- [ ] **Step 2: Add re-decision test**

Append:

```python
def test_review_decision_records_history_when_item_is_decided_again(client, admin_header, db_session):
    package, analysis, item = create_review_item(client, admin_header, db_session)

    first = client.post(
        f"/api/v1/modules/load-plan/review-queue/{item['id']}/decide",
        json={"decision_status": "NEEDS_MANUAL_ACTION", "decision_note": "Synthetic first note"},
        headers=admin_header,
    )
    second = client.post(
        f"/api/v1/modules/load-plan/review-queue/{item['id']}/decide",
        json={"decision_status": "EXCLUDED_FROM_CUTOVER", "decision_note": "Synthetic second note"},
        headers=admin_header,
    )

    refreshed_item = db_session.query(LoadPlanReviewItem).filter(LoadPlanReviewItem.id == item["id"]).one()
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] != second.json()["id"]
    assert db_session.query(LoadPlanReviewDecision).count() == 2
    assert refreshed_item.status == "EXCLUDED_FROM_CUTOVER"
    assert second.json()["review_item"]["latest_decision_id"] == second.json()["id"]
    assert second.json()["review_item"]["latest_decision_status"] == "EXCLUDED_FROM_CUTOVER"
```

- [ ] **Step 3: Add evidence note privacy assertion**

Append:

```python
def test_review_decision_evidence_tracks_note_presence_without_copying_note(client, admin_header, db_session):
    package, analysis, item = create_review_item(client, admin_header, db_session)

    response = client.post(
        f"/api/v1/modules/load-plan/review-queue/{item['id']}/decide",
        json={"decision_status": "REJECTED", "decision_note": "Synthetic private decision note"},
        headers=admin_header,
    )

    evidence = db_session.query(Evidence).filter(Evidence.id == response.json()["evidence_id"]).one()
    summary = json.loads(evidence.summary_json)
    assert response.status_code == 200
    assert summary["decision_note_present"] is True
    assert "Synthetic private decision note" not in evidence.summary_json
    assert "OTM1.ACC_COST_001" not in evidence.summary_json
```

- [ ] **Step 4: Run error/re-decision tests**

Run:

```bash
python -m pytest tests/test_load_plan_review_decisions.py::test_review_decision_rejects_invalid_status_without_changing_item tests/test_load_plan_review_decisions.py::test_review_decision_rejects_missing_item tests/test_load_plan_review_decisions.py::test_review_decision_records_history_when_item_is_decided_again tests/test_load_plan_review_decisions.py::test_review_decision_evidence_tracks_note_presence_without_copying_note -q
```

Expected: PASS.

- [ ] **Step 5: Commit errors and re-decisions**

```bash
git add src/otm_workbench/modules/load_plan/review_queue.py tests/test_load_plan_review_decisions.py
git commit -m "test: cover review decision errors and history"
```

## Task 5: README And Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README**

Add after the Setup Review Queue paragraph:

```markdown
The Load Plan Review Decisions slice records append-only decisions for review
queue items, updates item status, and creates client-safe evidence/audit/event
metadata without calculating cutover readiness, changing package status, or
claiming OTM validation.
```

Update the focused verification command to include:

```powershell
tests/test_load_plan_review_decisions.py
```

- [ ] **Step 2: Run focused tests**

Run:

```bash
python -m pytest tests/test_load_plan_review_decisions.py -q
```

Expected: all Review Decisions tests PASS.

- [ ] **Step 3: Run full verification**

Run:

```bash
python -m pytest -q
python -m alembic upgrade head
python -m ruff check src tests
```

Expected:

- pytest passes all tests.
- Alembic upgrades through `c7d2f4a9e1b5`.
- Ruff reports no issues.

- [ ] **Step 4: Commit docs**

```bash
git add README.md
git commit -m "docs: document load plan review decisions"
```

## Final Acceptance Checklist

- [ ] `load_plan_review_decisions` exists after metadata reset.
- [ ] `POST /review-queue/{item_id}/decide` creates a decision row.
- [ ] Review item status updates to the latest decision status.
- [ ] Evidence, audit log, and domain event are created.
- [ ] Decision response includes updated item and latest decision metadata.
- [ ] Review queue list/detail expose latest decision fields.
- [ ] Invalid status returns 400 and does not mutate item status.
- [ ] Missing item returns 404.
- [ ] Re-deciding creates append-only history and updates latest status.
- [ ] Audit/event payloads do not include raw row values or decision notes.
- [ ] Evidence stores `decision_note_present` without copying note text.
- [ ] No cutover readiness, package status transition, OTM upload, CSVUTIL execution, external Oracle call, or UI was added.
