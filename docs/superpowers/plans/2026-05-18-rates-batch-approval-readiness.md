# Rates Batch Approval And Readiness Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add backend readiness and approval gates for Rates batches, with client-safe evidence, audit, and domain event records.

**Architecture:** Add a focused `modules/rates/approval.py` service that computes readiness from existing batch tables, rows, issues, and export evidence; then approves eligible batches idempotently. Expose thin routes in `modules/rates/routes.py` for readiness and approval.

**Tech Stack:** Python, FastAPI, SQLAlchemy, SQLite, existing platform metadata models, pytest, Ruff.

---

## File Structure

- Create `src/otm_workbench/modules/rates/approval.py`: readiness calculation, approval preconditions, idempotent approval, evidence/audit/event creation.
- Modify `src/otm_workbench/modules/rates/routes.py`: add `GET /readiness` and `POST /approve`.
- Create `tests/test_rates_batch_approval.py`: readiness and approval tests.
- Modify `README.md`: add one sentence to the Rates verification section.

No Alembic migration is required. Approval metadata uses existing `RateBatch.approved_at`, `RateBatch.summary_json`, `Evidence`, `AuditLog`, and `DomainEvent`.

Before implementing, confirm the OTM table assumptions against `OTM_RESOURCES/DATA_DICT26B/data_dictionary/json/data_dict`. The test payloads in this plan use synthetic `OTM1` values only and should not introduce real client names or production identifiers.

---

## Task 1: Readiness Service And Endpoint

**Files:**
- Create: `src/otm_workbench/modules/rates/approval.py`
- Modify: `src/otm_workbench/modules/rates/routes.py`
- Test: `tests/test_rates_batch_approval.py`

- [ ] **Step 1: Write failing readiness tests**

Confirm the Data Dictionary metadata exists before writing the tests:

```bash
rg -n '"ACCESSORIAL_COST"' OTM_RESOURCES/DATA_DICT26B/data_dictionary/json/data_dict
```

Expected: at least one match for the `ACCESSORIAL_COST` table definition.

Create `tests/test_rates_batch_approval.py`:

```python
def create_batch(client, admin_header, scenario_code="ACCESSORIAL_ONLY"):
    return client.post(
        "/api/v1/modules/rates/batches",
        json={"scenario_code": scenario_code, "name": "Synthetic approval batch", "domain_name": "OTM1"},
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
                        }
                    ],
                }
            ]
        },
        headers=admin_header,
    )


def test_readiness_returns_blockers_for_draft_batch(client, admin_header):
    batch = create_batch(client, admin_header)

    response = client.get(
        f"/api/v1/modules/rates/batches/{batch['id']}/readiness",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ready_for_approval"] is False
    assert "BATCH_NOT_VALIDATED" in payload["blockers"]
    assert payload["issue_summary"] == {"errors": 0, "warnings": 0, "infos": 0}


def test_readiness_returns_counts_and_export_flag(client, admin_header):
    batch = create_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])
    client.post(f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview", headers=admin_header)
    export = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/export-csv",
        headers=admin_header,
    )
    assert export.status_code == 200

    response = client.get(
        f"/api/v1/modules/rates/batches/{batch['id']}/readiness",
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ready_for_approval"] is True
    assert payload["ready_for_export"] is True
    assert payload["table_count"] == 1
    assert payload["row_count"] == 1
    assert payload["has_export_artifact"] is True
    assert payload["blockers"] == []
    assert "approve" in payload["next_actions"]
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/test_rates_batch_approval.py::test_readiness_returns_blockers_for_draft_batch tests/test_rates_batch_approval.py::test_readiness_returns_counts_and_export_flag -q
```

Expected: FAIL with missing route/module.

- [ ] **Step 3: Implement readiness service**

Create `src/otm_workbench/modules/rates/approval.py`:

```python
from dataclasses import dataclass

from sqlalchemy.orm import Session

from otm_workbench.models import RateBatch, RateBatchIssue, RateBatchTable
from otm_workbench.modules.rates.exports import list_batch_export_artifacts


@dataclass(frozen=True)
class RateBatchReadiness:
    batch_id: str
    status: str
    ready_for_approval: bool
    ready_for_export: bool
    issue_summary: dict[str, int]
    table_count: int
    row_count: int
    has_export_artifact: bool
    blockers: list[str]
    next_actions: list[str]


def issue_summary(db: Session, batch_id: str) -> dict[str, int]:
    issues = db.query(RateBatchIssue).filter(RateBatchIssue.batch_id == batch_id).all()
    return {
        "errors": sum(1 for issue in issues if issue.severity == "ERROR"),
        "warnings": sum(1 for issue in issues if issue.severity == "WARNING"),
        "infos": sum(1 for issue in issues if issue.severity == "INFO"),
    }


def table_and_row_counts(db: Session, batch_id: str) -> tuple[int, int]:
    tables = db.query(RateBatchTable).filter(RateBatchTable.batch_id == batch_id).all()
    return len(tables), sum(table.row_count for table in tables)


def get_rate_batch_readiness(db: Session, batch: RateBatch) -> RateBatchReadiness:
    summary = issue_summary(db, batch.id)
    table_count, row_count = table_and_row_counts(db, batch.id)
    has_export_artifact = bool(list_batch_export_artifacts(db, batch.id))
    blockers: list[str] = []

    if batch.status == "DRAFT":
        blockers.append("BATCH_NOT_VALIDATED")
    if summary["errors"] > 0:
        blockers.append("HAS_ERROR_ISSUES")
    if table_count == 0:
        blockers.append("NO_TABLES")
    if row_count == 0:
        blockers.append("NO_ROWS")
    if batch.status == "APPROVED":
        blockers.append("ALREADY_APPROVED")

    approval_candidate_statuses = {"VALIDATED", "EXPORT_PREVIEWED", "EXPORTED"}
    export_candidate_statuses = {"VALIDATED", "EXPORT_PREVIEWED", "APPROVED"}
    ready_for_approval = (
        batch.status in approval_candidate_statuses
        and summary["errors"] == 0
        and table_count > 0
        and row_count > 0
    )
    ready_for_export = (
        batch.status in export_candidate_statuses
        and summary["errors"] == 0
        and table_count > 0
        and row_count > 0
    )

    next_actions: list[str] = []
    if ready_for_export and not has_export_artifact:
        next_actions.append("export_csv")
    if ready_for_approval:
        next_actions.append("approve")

    return RateBatchReadiness(
        batch_id=batch.id,
        status=batch.status,
        ready_for_approval=ready_for_approval,
        ready_for_export=ready_for_export,
        issue_summary=summary,
        table_count=table_count,
        row_count=row_count,
        has_export_artifact=has_export_artifact,
        blockers=blockers,
        next_actions=next_actions,
    )
```

- [ ] **Step 4: Add readiness route**

In `routes.py`, import `get_rate_batch_readiness` and add:

```python
@router.get("/batches/{batch_id}/readiness")
def get_rates_batch_readiness(batch_id: str, db: Session = Depends(get_db), user: User = Depends(require_user)):
    batch = db.query(RateBatch).filter(RateBatch.id == batch_id).first()
    if batch is None:
        raise HTTPException(status_code=404, detail="Rate batch not found.")
    return get_rate_batch_readiness(db, batch).__dict__
```

- [ ] **Step 5: Run readiness tests**

Run:

```bash
python -m pytest tests/test_rates_batch_approval.py::test_readiness_returns_blockers_for_draft_batch tests/test_rates_batch_approval.py::test_readiness_returns_counts_and_export_flag -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/otm_workbench/modules/rates/approval.py src/otm_workbench/modules/rates/routes.py tests/test_rates_batch_approval.py
git commit -m "feat: add rates batch readiness"
```

---

## Task 2: Approval Preconditions And Status

**Files:**
- Modify: `src/otm_workbench/modules/rates/approval.py`
- Modify: `src/otm_workbench/modules/rates/routes.py`
- Test: `tests/test_rates_batch_approval.py`

- [ ] **Step 1: Add failing approval precondition tests**

Append to `tests/test_rates_batch_approval.py`:

```python
def test_approval_rejects_draft_batch(client, admin_header):
    batch = create_batch(client, admin_header)

    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/approve",
        json={"approval_note": "Reviewed for synthetic CRP package"},
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "not ready" in response.json()["message"].lower()


def test_approval_rejects_batch_with_error_issues(client, admin_header):
    batch = create_batch(client, admin_header, scenario_code="RATE_GEO_ONLY")
    add_accessorial_table(client, admin_header, batch["id"])
    client.post(f"/api/v1/modules/rates/batches/{batch['id']}/validate", headers=admin_header)

    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/approve",
        json={"approval_note": "Reviewed for synthetic CRP package"},
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "error" in response.json()["message"].lower()


def test_approval_sets_status_and_summary(client, admin_header, db_session):
    batch = create_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])
    client.post(f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview", headers=admin_header)

    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/approve",
        json={"approval_note": "Reviewed for synthetic CRP package"},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "APPROVED"
    assert payload["approved_at"] is not None
    assert payload["approved_by"] == "admin@example.com"
    refreshed = client.get(f"/api/v1/modules/rates/batches/{batch['id']}", headers=admin_header)
    assert refreshed.json()["status"] == "APPROVED"
    assert "Reviewed for synthetic CRP package" in refreshed.json()["summary_json"]
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
python -m pytest tests/test_rates_batch_approval.py::test_approval_rejects_draft_batch tests/test_rates_batch_approval.py::test_approval_rejects_batch_with_error_issues tests/test_rates_batch_approval.py::test_approval_sets_status_and_summary -q
```

Expected: FAIL with missing route.

- [ ] **Step 3: Add request dataclass and approval status function**

In `approval.py`, add:

```python
import json

from otm_workbench.models import utcnow


def approve_rate_batch_status(
    db: Session,
    *,
    batch: RateBatch,
    approved_by: str,
    approval_note: str = "",
) -> dict[str, object]:
    readiness = get_rate_batch_readiness(db, batch)
    if readiness.issue_summary["errors"] > 0:
        raise ValueError("Rate batch has ERROR issues and cannot be approved.")
    if not readiness.ready_for_approval:
        raise ValueError("Rate batch is not ready for approval.")

    approved_at = utcnow()
    summary = json.loads(batch.summary_json or "{}")
    summary["approval"] = {
        "approved_by": approved_by,
        "approved_at": approved_at.isoformat(),
        "approval_note": approval_note,
    }
    batch.status = "APPROVED"
    batch.approved_at = approved_at
    batch.summary_json = json.dumps(summary, sort_keys=True)
    db.commit()
    return {
        "batch_id": batch.id,
        "status": batch.status,
        "approved_at": approved_at.isoformat(),
        "approved_by": approved_by,
        "evidence_id": None,
        "readiness": get_rate_batch_readiness(db, batch).__dict__,
    }
```

- [ ] **Step 4: Add approve route**

In `routes.py`, add:

```python
class ApproveRateBatchRequest(BaseModel):
    approval_note: str = ""
```

Import `approve_rate_batch_status`, then add:

```python
@router.post("/batches/{batch_id}/approve")
def approve_rates_batch(
    batch_id: str,
    payload: ApproveRateBatchRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    batch = db.query(RateBatch).filter(RateBatch.id == batch_id).first()
    if batch is None:
        raise HTTPException(status_code=404, detail="Rate batch not found.")
    try:
        return approve_rate_batch_status(
            db,
            batch=batch,
            approved_by=user.email,
            approval_note=payload.approval_note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
```

- [ ] **Step 5: Run approval precondition tests**

Run:

```bash
python -m pytest tests/test_rates_batch_approval.py::test_approval_rejects_draft_batch tests/test_rates_batch_approval.py::test_approval_rejects_batch_with_error_issues tests/test_rates_batch_approval.py::test_approval_sets_status_and_summary -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/otm_workbench/modules/rates/approval.py src/otm_workbench/modules/rates/routes.py tests/test_rates_batch_approval.py
git commit -m "feat: approve rates batches"
```

---

## Task 3: Approval Evidence, Audit, And Event

**Files:**
- Modify: `src/otm_workbench/modules/rates/approval.py`
- Test: `tests/test_rates_batch_approval.py`

- [ ] **Step 1: Add failing metadata test**

Append to `tests/test_rates_batch_approval.py`:

```python
from otm_workbench.models import AuditLog, DomainEvent, Evidence


def test_approval_creates_evidence_audit_and_event(client, admin_header, db_session):
    batch = create_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])
    client.post(f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview", headers=admin_header)

    response = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/approve",
        json={"approval_note": "Reviewed for synthetic CRP package"},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    evidence = db_session.query(Evidence).filter(Evidence.id == payload["evidence_id"]).one()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "rates.batch.approve").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "rates.batch.approved").one()

    assert evidence.client_safe is True
    assert evidence.evidence_type == "rates_batch_approval"
    assert evidence.artifact_id is None
    assert "OTM1.ACC_COST_001" not in evidence.summary_json
    assert audit.target_id == batch["id"]
    assert event.aggregate_id == batch["id"]
    assert event.status == "PENDING"
```

- [ ] **Step 2: Run metadata test to verify failure**

Run:

```bash
python -m pytest tests/test_rates_batch_approval.py::test_approval_creates_evidence_audit_and_event -q
```

Expected: FAIL because approval does not create evidence/audit/event yet.

- [ ] **Step 3: Create metadata records on approval**

In `approval.py`, import `AuditLog`, `DomainEvent`, `Evidence`, and `list_batch_export_evidence`.

Add helper:

```python
def latest_export_references(db: Session, batch_id: str) -> tuple[str | None, str | None]:
    export_evidence = list_batch_export_evidence(db, batch_id)
    if not export_evidence:
        return None, None
    latest = export_evidence[0]
    return latest.artifact_id, latest.manifest_id
```

In `approve_rate_batch_status`, before `db.commit()`, create:

```python
artifact_id, manifest_id = latest_export_references(db, batch.id)
evidence_summary = {
    "source_entity_type": "rate_batch",
    "source_entity_id": batch.id,
    "scenario_code": batch.scenario_code,
    "domain_name": batch.domain_name,
    "approved_by": approved_by,
    "approved_at": approved_at.isoformat(),
    "issue_summary": readiness.issue_summary,
    "table_count": readiness.table_count,
    "row_count": readiness.row_count,
    "has_export_artifact": artifact_id is not None,
    "approval_note": approval_note,
}
evidence = Evidence(
    source_module="rates",
    evidence_type="rates_batch_approval",
    summary_json=json.dumps(evidence_summary, sort_keys=True),
    artifact_id=artifact_id,
    manifest_id=manifest_id,
    client_safe=True,
    sensitivity_level="client_safe",
)
db.add(evidence)
db.flush()

audit = AuditLog(
    actor_user_id=approved_by,
    action="rates.batch.approve",
    target_type="rate_batch",
    target_id=batch.id,
    metadata_json=json.dumps(
        {
            "evidence_id": evidence.id,
            "approved_by": approved_by,
            "issue_summary": readiness.issue_summary,
        },
        sort_keys=True,
    ),
)
db.add(audit)

event = DomainEvent(
    event_type="rates.batch.approved",
    source_module="rates",
    project_id=batch.project_id,
    aggregate_type="rate_batch",
    aggregate_id=batch.id,
    payload_json=json.dumps(
        {
            "evidence_id": evidence.id,
            "approved_by": approved_by,
            "status": "APPROVED",
        },
        sort_keys=True,
    ),
    status="PENDING",
)
db.add(event)
```

Return `evidence.id`.

- [ ] **Step 4: Run metadata test**

Run:

```bash
python -m pytest tests/test_rates_batch_approval.py::test_approval_creates_evidence_audit_and_event -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/otm_workbench/modules/rates/approval.py tests/test_rates_batch_approval.py
git commit -m "feat: record rates approval evidence"
```

---

## Task 4: Idempotent Approval

**Files:**
- Modify: `src/otm_workbench/modules/rates/approval.py`
- Test: `tests/test_rates_batch_approval.py`

- [ ] **Step 1: Add failing idempotency test**

Append to `tests/test_rates_batch_approval.py`:

```python
def test_repeated_approval_is_idempotent(client, admin_header, db_session):
    batch = create_batch(client, admin_header)
    add_accessorial_table(client, admin_header, batch["id"])
    client.post(f"/api/v1/modules/rates/batches/{batch['id']}/csv-preview", headers=admin_header)

    first = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/approve",
        json={"approval_note": "Reviewed once"},
        headers=admin_header,
    )
    second = client.post(
        f"/api/v1/modules/rates/batches/{batch['id']}/approve",
        json={"approval_note": "Reviewed twice"},
        headers=admin_header,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["evidence_id"] == second.json()["evidence_id"]
    assert db_session.query(Evidence).filter(Evidence.evidence_type == "rates_batch_approval").count() == 1
    assert db_session.query(AuditLog).filter(AuditLog.action == "rates.batch.approve").count() == 1
    assert db_session.query(DomainEvent).filter(DomainEvent.event_type == "rates.batch.approved").count() == 1
```

- [ ] **Step 2: Run idempotency test to verify failure**

Run:

```bash
python -m pytest tests/test_rates_batch_approval.py::test_repeated_approval_is_idempotent -q
```

Expected: FAIL because repeated approval is rejected or creates duplicates.

- [ ] **Step 3: Implement idempotency**

In `approval.py`, add:

```python
def existing_approval_evidence(db: Session, batch_id: str) -> Evidence | None:
    needle = f'"source_entity_id": "{batch_id}"'
    return (
        db.query(Evidence)
        .filter(Evidence.source_module == "rates")
        .filter(Evidence.evidence_type == "rates_batch_approval")
        .filter(Evidence.summary_json.contains(needle))
        .order_by(Evidence.created_at.desc())
        .first()
    )
```

At the start of `approve_rate_batch_status`, if `batch.status == "APPROVED"`:

```python
existing = existing_approval_evidence(db, batch.id)
summary = json.loads(batch.summary_json or "{}")
approval = summary.get("approval", {})
return {
    "batch_id": batch.id,
    "status": batch.status,
    "approved_at": approval.get("approved_at") or (batch.approved_at.isoformat() if batch.approved_at else None),
    "approved_by": approval.get("approved_by") or approved_by,
    "evidence_id": existing.id if existing else None,
    "readiness": get_rate_batch_readiness(db, batch).__dict__,
}
```

Do not create new evidence/audit/event in this path.

- [ ] **Step 4: Run approval tests**

Run:

```bash
python -m pytest tests/test_rates_batch_approval.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/otm_workbench/modules/rates/approval.py tests/test_rates_batch_approval.py
git commit -m "feat: make rates approval idempotent"
```

---

## Task 5: Documentation And Full Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README**

Add:

```markdown
The Rates Batch Approval slice adds backend readiness and approval gates for
validated/exported batches, with client-safe approval evidence, audit, and domain
event records.
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
git commit -m "docs: document rates batch approval"
```

Skip if README was already committed in a prior task.

---

## Self-Review

Spec coverage:

- Readiness endpoint and blockers: Task 1.
- Approval endpoint and preconditions: Task 2.
- Approval evidence, audit, and domain event: Task 3.
- Idempotency: Task 4.
- Full verification and docs: Task 5.

No UI, Load Plan, CSVUTIL, cutover readiness, real OTM upload, XML export, or new migration is included. Examples use synthetic `OTM1` values only.
