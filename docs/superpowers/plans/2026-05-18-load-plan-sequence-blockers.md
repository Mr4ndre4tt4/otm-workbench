# Load Plan Sequence Blockers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add backend/API support for generating Load Plan sequence snapshots with client-safe blockers from package metadata, latest ZIP Analysis, review decisions, and local OTM Data Dictionary foreign keys.

**Architecture:** Add a persisted `LoadPlanSequenceSnapshot` model and migration, then implement a focused `modules/load_plan/sequence.py` service that validates one package, reads Data Dictionary JSON, derives sequence rows and blockers, creates evidence/audit/event records, and serializes snapshots. Extend the existing Load Plan router with snapshot create/list/detail/latest endpoints.

**Tech Stack:** Python, FastAPI, Pydantic, SQLAlchemy ORM, Alembic, pytest, stdlib `json`/`pathlib`, existing Load Plan package, ZIP Analysis, and Review Queue models.

---

## File Structure

- Modify `src/otm_workbench/models.py`: add `LoadPlanSequenceSnapshot` after `LoadPlanReviewDecision`.
- Create `migrations/versions/f2a6c8d1e9b4_load_plan_sequence_snapshots.py`: create/drop `load_plan_sequence_snapshots`.
- Create `src/otm_workbench/modules/load_plan/sequence.py`: sequence snapshot service, Data Dictionary readers, blocker derivation, serializers.
- Modify `src/otm_workbench/modules/load_plan/routes.py`: add request model and sequence endpoints.
- Create `tests/test_load_plan_sequence_blockers.py`: model, service/API, blockers, Data Dictionary dependency, history, and safety tests.
- Modify `README.md`: document the backend-only Load Plan Sequence Blockers slice and add the test file to the verification command.

No UI, cutover readiness, OTM upload, CSVUTIL runtime execution, package status transitions, or cross-package scheduling is included.

---

### Task 1: Persistence Model And Migration

**Files:**
- Modify: `src/otm_workbench/models.py`
- Create: `migrations/versions/f2a6c8d1e9b4_load_plan_sequence_snapshots.py`
- Create: `tests/test_load_plan_sequence_blockers.py`

- [ ] **Step 1: Write the failing table test**

Create `tests/test_load_plan_sequence_blockers.py`:

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
    LoadPlanPackage,
    LoadPlanReviewDecision,
    LoadPlanReviewItem,
    LoadPlanSequenceSnapshot,
)


def create_rate_batch(client, admin_header, scenario_code="ACCESSORIAL_ONLY"):
    response = client.post(
        "/api/v1/modules/rates/batches",
        json={"scenario_code": scenario_code, "name": "Synthetic sequence batch", "domain_name": "OTM1"},
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
        json={"approval_note": "Reviewed for synthetic sequence package"},
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
    rewritten_path = artifact_path.with_suffix(".sequence-blockers.zip")
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


def create_review_item(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    rewrite_export_with_unknown_column(db_session, export)
    analysis = create_zip_analysis(client, admin_header, package)
    review = client.post(
        f"/api/v1/modules/load-plan/review-queue/from-zip-analysis/{analysis['id']}",
        headers=admin_header,
    )
    assert review.status_code == 200
    return package, analysis, review.json()["items"][0]


def test_load_plan_sequence_snapshots_table_exists_after_metadata_reset():
    tables = set(inspect(engine).get_table_names())

    assert "load_plan_sequence_snapshots" in tables
```

- [ ] **Step 2: Run the failing test**

Run:

```powershell
python -m pytest tests/test_load_plan_sequence_blockers.py::test_load_plan_sequence_snapshots_table_exists_after_metadata_reset -q
```

Expected: fail during import because `LoadPlanSequenceSnapshot` does not exist.

- [ ] **Step 3: Add the model**

Append after `LoadPlanReviewDecision` in `src/otm_workbench/models.py`:

```python
class LoadPlanSequenceSnapshot(Base, TimestampMixin):
    __tablename__ = "load_plan_sequence_snapshots"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    package_id: Mapped[str] = mapped_column(ForeignKey("load_plan_packages.id"), index=True)
    status: Mapped[str] = mapped_column(String, default="BLOCKED", index=True)
    sequence_json: Mapped[str] = mapped_column(Text, default="[]")
    blockers_json: Mapped[str] = mapped_column(Text, default="[]")
    summary_json: Mapped[str] = mapped_column(Text, default="{}")
    evidence_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    generated_by: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
```

- [ ] **Step 4: Add the Alembic migration**

Create `migrations/versions/f2a6c8d1e9b4_load_plan_sequence_snapshots.py`:

```python
"""load plan sequence snapshots

Revision ID: f2a6c8d1e9b4
Revises: c7d2f4a9e1b5
Create Date: 2026-05-18 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f2a6c8d1e9b4"
down_revision: str | None = "c7d2f4a9e1b5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "load_plan_sequence_snapshots",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=True),
        sa.Column("environment_id", sa.String(), nullable=True),
        sa.Column("profile_id", sa.String(), nullable=True),
        sa.Column("package_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("sequence_json", sa.Text(), nullable=False),
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
        "status",
        "evidence_id",
        "generated_by",
        "generated_at",
    ]:
        op.create_index(
            f"ix_load_plan_sequence_snapshots_{column}",
            "load_plan_sequence_snapshots",
            [column],
        )


def downgrade() -> None:
    for column in [
        "generated_at",
        "generated_by",
        "evidence_id",
        "status",
        "package_id",
        "profile_id",
        "environment_id",
        "project_id",
    ]:
        op.drop_index(f"ix_load_plan_sequence_snapshots_{column}", table_name="load_plan_sequence_snapshots")
    op.drop_table("load_plan_sequence_snapshots")
```

- [ ] **Step 5: Run the table test again**

Run:

```powershell
python -m pytest tests/test_load_plan_sequence_blockers.py::test_load_plan_sequence_snapshots_table_exists_after_metadata_reset -q
```

Expected: pass.

- [ ] **Step 6: Commit persistence**

```powershell
git add src/otm_workbench/models.py migrations/versions/f2a6c8d1e9b4_load_plan_sequence_snapshots.py tests/test_load_plan_sequence_blockers.py
git commit -m "feat: add load plan sequence snapshot model"
```

---

### Task 2: Sequence Service, Data Dictionary Dependencies, And Core Snapshot

**Files:**
- Create: `src/otm_workbench/modules/load_plan/sequence.py`
- Modify: `tests/test_load_plan_sequence_blockers.py`

- [ ] **Step 1: Add failing service/API-oriented tests for missing package and successful snapshot**

Append to `tests/test_load_plan_sequence_blockers.py`:

```python
def test_sequence_snapshot_rejects_missing_package(client, admin_header):
    response = client.post(
        "/api/v1/modules/load-plan/sequence/snapshots",
        json={"package_id": "missing_package"},
        headers=admin_header,
    )

    assert response.status_code == 404


def test_sequence_snapshot_creates_snapshot_evidence_audit_and_event(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)

    response = client.post(
        "/api/v1/modules/load-plan/sequence/snapshots",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["package_id"] == package["id"]
    assert payload["status"] == "BLOCKED"
    assert payload["generated_by"] == "admin@example.com"
    assert payload["sequence"][0]["table_name"] == "ACCESSORIAL_COST"
    assert payload["sequence"][0]["dictionary_table_found"] is True
    assert "ACCESSORIAL_CODE" in payload["sequence"][0]["parent_tables"]
    assert "ACCESSORIAL_CODE" in payload["sequence"][0]["missing_parent_tables_in_package"]
    assert "ZIP_ANALYSIS_MISSING" in [item["code"] for item in payload["blockers"]]
    assert "PACKAGE_PARENT_TABLE_MISSING" in [item["code"] for item in payload["blockers"]]
    snapshot = db_session.query(LoadPlanSequenceSnapshot).filter(LoadPlanSequenceSnapshot.id == payload["id"]).one()
    evidence = db_session.query(Evidence).filter(Evidence.id == snapshot.evidence_id).one()
    audit = db_session.query(AuditLog).filter(AuditLog.action == "load_plan.sequence.snapshot.generate").one()
    event = db_session.query(DomainEvent).filter(DomainEvent.event_type == "load_plan.sequence.snapshot.generated").one()
    assert evidence.evidence_type == "load_plan_sequence_snapshot"
    assert evidence.client_safe is True
    assert audit.target_id == snapshot.id
    assert event.aggregate_id == snapshot.id
    assert "OTM1.ACC_COST_001" not in evidence.summary_json
    assert "OTM1.ACC_COST_001" not in audit.metadata_json
    assert "OTM1.ACC_COST_001" not in event.payload_json
```

- [ ] **Step 2: Run the failing tests**

Run:

```powershell
python -m pytest tests/test_load_plan_sequence_blockers.py::test_sequence_snapshot_rejects_missing_package tests/test_load_plan_sequence_blockers.py::test_sequence_snapshot_creates_snapshot_evidence_audit_and_event -q
```

Expected: fail with 404 because the route does not exist.

- [ ] **Step 3: Create the sequence service**

Create `src/otm_workbench/modules/load_plan/sequence.py`:

```python
import json
from pathlib import Path

from sqlalchemy.orm import Session

from otm_workbench.models import (
    AuditLog,
    DomainEvent,
    Evidence,
    LoadPlanPackage,
    LoadPlanReviewDecision,
    LoadPlanReviewItem,
    LoadPlanSequenceSnapshot,
    LoadPlanZipAnalysis,
    utcnow,
)
from otm_workbench.modules.load_plan.packages import parse_json_list, parse_json_object


READY_STATUS = "READY_FOR_REVIEW"
BLOCKED_STATUS = "BLOCKED"


def blocker(
    code: str,
    severity: str,
    message: str,
    *,
    table_name: str | None = None,
    source_type: str | None = None,
    source_id: str | None = None,
    details: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "code": code,
        "severity": severity,
        "table_name": table_name,
        "source_type": source_type,
        "source_id": source_id,
        "message": message,
        "details": details or {},
    }


def serialize_sequence_snapshot(snapshot: LoadPlanSequenceSnapshot) -> dict[str, object]:
    return {
        "id": snapshot.id,
        "project_id": snapshot.project_id,
        "environment_id": snapshot.environment_id,
        "profile_id": snapshot.profile_id,
        "package_id": snapshot.package_id,
        "status": snapshot.status,
        "sequence": parse_json_list(snapshot.sequence_json),
        "blockers": parse_json_list(snapshot.blockers_json),
        "summary": parse_json_object(snapshot.summary_json),
        "evidence_id": snapshot.evidence_id,
        "generated_by": snapshot.generated_by,
        "generated_at": snapshot.generated_at.isoformat() if snapshot.generated_at else None,
    }


def latest_zip_analysis(db: Session, package_id: str) -> LoadPlanZipAnalysis | None:
    return (
        db.query(LoadPlanZipAnalysis)
        .filter(LoadPlanZipAnalysis.package_id == package_id)
        .order_by(LoadPlanZipAnalysis.analyzed_at.desc(), LoadPlanZipAnalysis.created_at.desc())
        .first()
    )


def latest_sequence_snapshot(db: Session, package_id: str) -> LoadPlanSequenceSnapshot | None:
    return (
        db.query(LoadPlanSequenceSnapshot)
        .filter(LoadPlanSequenceSnapshot.package_id == package_id)
        .order_by(LoadPlanSequenceSnapshot.generated_at.desc(), LoadPlanSequenceSnapshot.created_at.desc())
        .first()
    )


def load_dictionary_parent_tables(dictionary_root: Path, table_name: str) -> tuple[bool, list[str]]:
    normalized = table_name.upper()
    for path in (dictionary_root / f"{normalized}.json", dictionary_root / f"{normalized.lower()}.json"):
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
            parents = sorted(
                {
                    str(foreign_key.get("parentTableName", "")).upper()
                    for foreign_key in payload.get("foreignKeys", [])
                    if foreign_key.get("parentTableName")
                }
            )
            return True, parents
    return False, []


def latest_decision_for_item(db: Session, item_id: str) -> LoadPlanReviewDecision | None:
    return (
        db.query(LoadPlanReviewDecision)
        .filter(LoadPlanReviewDecision.review_item_id == item_id)
        .order_by(LoadPlanReviewDecision.decided_at.desc(), LoadPlanReviewDecision.created_at.desc())
        .first()
    )


def review_summary_for_table(db: Session, package_id: str, table_name: str) -> tuple[dict[str, int], list[dict[str, object]]]:
    summary = {
        "pending_count": 0,
        "needs_manual_action_count": 0,
        "rejected_count": 0,
        "excluded_from_cutover_count": 0,
        "confirmed_count": 0,
    }
    blockers: list[dict[str, object]] = []
    items = (
        db.query(LoadPlanReviewItem)
        .filter(LoadPlanReviewItem.package_id == package_id)
        .filter(LoadPlanReviewItem.table_name == table_name)
        .order_by(LoadPlanReviewItem.created_at)
        .all()
    )
    for item in items:
        decision = latest_decision_for_item(db, item.id)
        if decision is None or item.status == "PENDING_REVIEW":
            summary["pending_count"] += 1
            blockers.append(
                blocker(
                    "REVIEW_ITEM_PENDING",
                    "ERROR",
                    "A review item still needs a decision before later readiness checks.",
                    table_name=table_name,
                    source_type="load_plan_review_item",
                    source_id=item.id,
                )
            )
            continue
        if decision.decision_status == "CONFIRMED":
            summary["confirmed_count"] += 1
        elif decision.decision_status == "REJECTED":
            summary["rejected_count"] += 1
            blockers.append(blocker("REVIEW_ITEM_REJECTED", "ERROR", "A review item was rejected.", table_name=table_name, source_type="load_plan_review_decision", source_id=decision.id))
        elif decision.decision_status == "NEEDS_MANUAL_ACTION":
            summary["needs_manual_action_count"] += 1
            blockers.append(blocker("REVIEW_ITEM_NEEDS_MANUAL_ACTION", "ERROR", "A review item requires manual action.", table_name=table_name, source_type="load_plan_review_decision", source_id=decision.id))
        elif decision.decision_status == "EXCLUDED_FROM_CUTOVER":
            summary["excluded_from_cutover_count"] += 1
            blockers.append(blocker("REVIEW_ITEM_EXCLUDED_FROM_CUTOVER", "WARNING", "A review item was excluded from later cutover planning.", table_name=table_name, source_type="load_plan_review_decision", source_id=decision.id))
    return summary, blockers


def derive_next_actions(blockers: list[dict[str, object]]) -> list[str]:
    codes = {str(item["code"]) for item in blockers}
    actions: list[str] = []
    if "ZIP_ANALYSIS_MISSING" in codes:
        actions.append("run_zip_analysis")
    if "REVIEW_ITEM_PENDING" in codes:
        actions.append("decide_review_items")
    if "REVIEW_ITEM_NEEDS_MANUAL_ACTION" in codes:
        actions.append("resolve_manual_actions")
    if "REVIEW_ITEM_REJECTED" in codes:
        actions.append("remove_rejected_items_or_rework_package")
    if "REVIEW_ITEM_EXCLUDED_FROM_CUTOVER" in codes:
        actions.append("review_exclusions")
    if "PACKAGE_PARENT_TABLE_MISSING" in codes or "DICTIONARY_TABLE_MISSING" in codes:
        actions.append("review_package_dependencies")
    if not actions:
        actions.append("ready_for_later_readiness")
    return actions


def generate_sequence_snapshot(
    db: Session,
    *,
    package: LoadPlanPackage,
    dictionary_root: Path,
    generated_by: str,
) -> LoadPlanSequenceSnapshot:
    if package.status != "REGISTERED":
        raise ValueError("Load Plan package must be REGISTERED before sequence snapshot generation.")
    if not package.artifact_id or not package.manifest_id:
        raise ValueError("Load Plan package must reference source artifact and manifest before sequence snapshot generation.")
    load_sequence = parse_json_list(package.load_sequence_json)
    if not load_sequence:
        raise ValueError("Load Plan package must have a load sequence before sequence snapshot generation.")

    latest_analysis = latest_zip_analysis(db, package.id)
    package_tables = {str(item["table_name"]).upper() for item in load_sequence if item.get("table_name")}
    blockers: list[dict[str, object]] = []
    sequence_rows: list[dict[str, object]] = []
    findings = parse_json_list(latest_analysis.findings_json) if latest_analysis else []
    if latest_analysis is None:
        blockers.append(blocker("ZIP_ANALYSIS_MISSING", "ERROR", "No ZIP Analysis exists for this package.", source_type="load_plan_package", source_id=package.id))
    elif any(item.get("severity") == "ERROR" for item in findings):
        blockers.append(blocker("ZIP_ANALYSIS_HAS_ERRORS", "ERROR", "Latest ZIP Analysis has error findings.", source_type="load_plan_zip_analysis", source_id=latest_analysis.id))

    for item in load_sequence:
        table_name = str(item["table_name"]).upper()
        dictionary_found, parent_tables = load_dictionary_parent_tables(dictionary_root, table_name)
        missing_parent_tables = [parent for parent in parent_tables if parent not in package_tables]
        if not dictionary_found:
            blockers.append(blocker("DICTIONARY_TABLE_MISSING", "ERROR", "Table JSON is missing from the local OTM Data Dictionary.", table_name=table_name, source_type="load_plan_package", source_id=package.id))
        for parent in missing_parent_tables:
            blockers.append(
                blocker(
                    "PACKAGE_PARENT_TABLE_MISSING",
                    "ERROR",
                    "A Data Dictionary parent table is not present in this package sequence.",
                    table_name=table_name,
                    source_type="otm_data_dictionary",
                    source_id=parent,
                    details={"parent_table_name": parent},
                )
            )
        review_summary, review_blockers = review_summary_for_table(db, package.id, table_name)
        blockers.extend(review_blockers)
        table_findings = [finding for finding in findings if str(finding.get("table_name", "")).upper() == table_name]
        sequence_rows.append(
            {
                "position": int(item.get("position", 0)),
                "table_name": table_name,
                "row_count": int(item.get("row_count", 0)),
                "requirement_level": str(item.get("requirement_level", "OPTIONAL")),
                "dictionary_table_found": dictionary_found,
                "parent_tables": parent_tables,
                "missing_parent_tables_in_package": missing_parent_tables,
                "zip_analysis": {
                    "latest_analysis_id": latest_analysis.id if latest_analysis else None,
                    "finding_count": len(table_findings),
                    "error_count": sum(1 for finding in table_findings if finding.get("severity") == "ERROR"),
                    "warning_count": sum(1 for finding in table_findings if finding.get("severity") == "WARNING"),
                },
                "review": review_summary,
            }
        )

    error_count = sum(1 for item in blockers if item["severity"] == "ERROR")
    warning_count = sum(1 for item in blockers if item["severity"] == "WARNING")
    status = BLOCKED_STATUS if blockers else READY_STATUS
    summary = {
        "table_count": len(sequence_rows),
        "row_count": sum(int(item.get("row_count", 0)) for item in sequence_rows),
        "blocker_count": len(blockers),
        "error_count": error_count,
        "warning_count": warning_count,
        "next_actions": derive_next_actions(blockers),
    }
    generated_at = utcnow()
    snapshot = LoadPlanSequenceSnapshot(
        project_id=package.project_id,
        environment_id=package.environment_id,
        profile_id=package.profile_id,
        package_id=package.id,
        status=status,
        sequence_json=json.dumps(sequence_rows, sort_keys=True),
        blockers_json=json.dumps(blockers, sort_keys=True),
        summary_json=json.dumps(summary, sort_keys=True),
        generated_by=generated_by,
        generated_at=generated_at,
    )
    db.add(snapshot)
    db.flush()

    evidence_summary = {
        "source_entity_type": "load_plan_sequence_snapshot",
        "source_entity_id": snapshot.id,
        "package_id": package.id,
        "status": status,
        "table_count": summary["table_count"],
        "row_count": summary["row_count"],
        "blocker_count": summary["blocker_count"],
        "error_count": summary["error_count"],
        "warning_count": summary["warning_count"],
    }
    evidence = Evidence(
        project_id=package.project_id,
        source_module="load_plan",
        evidence_type="load_plan_sequence_snapshot",
        summary_json=json.dumps(evidence_summary, sort_keys=True),
        client_safe=True,
        sensitivity_level="client_safe",
    )
    db.add(evidence)
    db.flush()
    snapshot.evidence_id = evidence.id
    db.add(
        AuditLog(
            actor_user_id=generated_by,
            action="load_plan.sequence.snapshot.generate",
            target_type="load_plan_sequence_snapshot",
            target_id=snapshot.id,
            metadata_json=json.dumps(
                {
                    "package_id": package.id,
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
            event_type="load_plan.sequence.snapshot.generated",
            source_module="load_plan",
            project_id=package.project_id,
            aggregate_type="load_plan_sequence_snapshot",
            aggregate_id=snapshot.id,
            payload_json=json.dumps({"package_id": package.id, "status": status}, sort_keys=True),
            status="PENDING",
        )
    )
    db.commit()
    db.refresh(snapshot)
    return snapshot
```

- [ ] **Step 4: Add routes for snapshot creation**

Modify `src/otm_workbench/modules/load_plan/routes.py`:

```python
from otm_workbench.models import (
    CsvutilBuild,
    LoadPlanPackage,
    LoadPlanReviewItem,
    LoadPlanSequenceSnapshot,
    LoadPlanZipAnalysis,
    RateBatch,
    User,
)
from otm_workbench.modules.load_plan.sequence import (
    generate_sequence_snapshot,
    latest_sequence_snapshot,
    serialize_sequence_snapshot,
)
```

Add request model:

```python
class SequenceSnapshotRequest(BaseModel):
    package_id: str
```

Add route after summary or before review queue routes:

```python
@router.post("/sequence/snapshots")
def create_sequence_snapshot(
    payload: SequenceSnapshotRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    package = db.query(LoadPlanPackage).filter(LoadPlanPackage.id == payload.package_id).first()
    if package is None:
        raise HTTPException(status_code=404, detail="Load Plan package not found.")
    try:
        snapshot = generate_sequence_snapshot(
            db,
            package=package,
            dictionary_root=Path(get_settings().otm_data_dictionary_root),
            generated_by=user.email,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize_sequence_snapshot(snapshot)
```

- [ ] **Step 5: Run the tests**

Run:

```powershell
python -m pytest tests/test_load_plan_sequence_blockers.py::test_sequence_snapshot_rejects_missing_package tests/test_load_plan_sequence_blockers.py::test_sequence_snapshot_creates_snapshot_evidence_audit_and_event -q
```

Expected: pass.

- [ ] **Step 6: Commit core service**

```powershell
git add src/otm_workbench/modules/load_plan/sequence.py src/otm_workbench/modules/load_plan/routes.py tests/test_load_plan_sequence_blockers.py
git commit -m "feat: generate load plan sequence snapshots"
```

---

### Task 3: Review Decision Blockers, ZIP Analysis Findings, And Error Cases

**Files:**
- Modify: `src/otm_workbench/modules/load_plan/sequence.py`
- Modify: `tests/test_load_plan_sequence_blockers.py`

- [ ] **Step 1: Add failing tests for empty sequence and review decision statuses**

Append to `tests/test_load_plan_sequence_blockers.py`:

```python
def test_sequence_snapshot_rejects_package_with_empty_load_sequence(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    model = db_session.query(LoadPlanPackage).filter(LoadPlanPackage.id == package["id"]).one()
    model.load_sequence_json = "[]"
    db_session.commit()

    response = client.post(
        "/api/v1/modules/load-plan/sequence/snapshots",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 400
    assert "load sequence" in response.json()["detail"].lower()


def test_sequence_snapshot_marks_pending_review_item_as_blocker(client, admin_header, db_session):
    package, analysis, item = create_review_item(client, admin_header, db_session)

    response = client.post(
        "/api/v1/modules/load-plan/sequence/snapshots",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    codes = [blocker["code"] for blocker in payload["blockers"]]
    assert "REVIEW_ITEM_PENDING" in codes
    assert "decide_review_items" in payload["summary"]["next_actions"]
    assert item["details"]["column_name"] not in json.dumps(payload["blockers"])


def test_sequence_snapshot_uses_latest_review_decision_for_blockers(client, admin_header, db_session):
    package, analysis, item = create_review_item(client, admin_header, db_session)
    first = client.post(
        f"/api/v1/modules/load-plan/review-queue/{item['id']}/decide",
        json={"decision_status": "CONFIRMED", "decision_note": "Synthetic confirmed note"},
        headers=admin_header,
    )
    second = client.post(
        f"/api/v1/modules/load-plan/review-queue/{item['id']}/decide",
        json={"decision_status": "NEEDS_MANUAL_ACTION", "decision_note": "Synthetic manual action note"},
        headers=admin_header,
    )
    assert first.status_code == 200
    assert second.status_code == 200

    response = client.post(
        "/api/v1/modules/load-plan/sequence/snapshots",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    codes = [blocker["code"] for blocker in payload["blockers"]]
    assert "REVIEW_ITEM_NEEDS_MANUAL_ACTION" in codes
    assert "REVIEW_ITEM_PENDING" not in codes
    assert "resolve_manual_actions" in payload["summary"]["next_actions"]
    assert "Synthetic manual action note" not in json.dumps(payload)
    assert db_session.query(LoadPlanReviewDecision).count() == 2


def test_sequence_snapshot_confirmed_review_item_does_not_create_review_blocker(client, admin_header, db_session):
    package, analysis, item = create_review_item(client, admin_header, db_session)
    decision = client.post(
        f"/api/v1/modules/load-plan/review-queue/{item['id']}/decide",
        json={"decision_status": "CONFIRMED", "decision_note": "Synthetic confirmation"},
        headers=admin_header,
    )
    assert decision.status_code == 200

    response = client.post(
        "/api/v1/modules/load-plan/sequence/snapshots",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    codes = [blocker["code"] for blocker in response.json()["blockers"]]
    assert "REVIEW_ITEM_PENDING" not in codes
    assert "REVIEW_ITEM_REJECTED" not in codes
    assert "REVIEW_ITEM_NEEDS_MANUAL_ACTION" not in codes
```

- [ ] **Step 2: Add failing tests for rejected and excluded decisions**

Append:

```python
def test_sequence_snapshot_rejected_review_item_creates_error_blocker(client, admin_header, db_session):
    package, analysis, item = create_review_item(client, admin_header, db_session)
    response = client.post(
        f"/api/v1/modules/load-plan/review-queue/{item['id']}/decide",
        json={"decision_status": "REJECTED", "decision_note": "Synthetic rejection"},
        headers=admin_header,
    )
    assert response.status_code == 200

    snapshot = client.post(
        "/api/v1/modules/load-plan/sequence/snapshots",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert snapshot.status_code == 200
    blockers = snapshot.json()["blockers"]
    assert any(item["code"] == "REVIEW_ITEM_REJECTED" and item["severity"] == "ERROR" for item in blockers)
    assert "remove_rejected_items_or_rework_package" in snapshot.json()["summary"]["next_actions"]


def test_sequence_snapshot_excluded_review_item_creates_warning_blocker(client, admin_header, db_session):
    package, analysis, item = create_review_item(client, admin_header, db_session)
    response = client.post(
        f"/api/v1/modules/load-plan/review-queue/{item['id']}/decide",
        json={"decision_status": "EXCLUDED_FROM_CUTOVER", "decision_note": "Synthetic exclusion"},
        headers=admin_header,
    )
    assert response.status_code == 200

    snapshot = client.post(
        "/api/v1/modules/load-plan/sequence/snapshots",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert snapshot.status_code == 200
    blockers = snapshot.json()["blockers"]
    assert any(item["code"] == "REVIEW_ITEM_EXCLUDED_FROM_CUTOVER" and item["severity"] == "WARNING" for item in blockers)
    assert "review_exclusions" in snapshot.json()["summary"]["next_actions"]
```

- [ ] **Step 3: Run the focused tests**

Run:

```powershell
python -m pytest tests/test_load_plan_sequence_blockers.py::test_sequence_snapshot_rejects_package_with_empty_load_sequence tests/test_load_plan_sequence_blockers.py::test_sequence_snapshot_marks_pending_review_item_as_blocker tests/test_load_plan_sequence_blockers.py::test_sequence_snapshot_uses_latest_review_decision_for_blockers tests/test_load_plan_sequence_blockers.py::test_sequence_snapshot_confirmed_review_item_does_not_create_review_blocker tests/test_load_plan_sequence_blockers.py::test_sequence_snapshot_rejected_review_item_creates_error_blocker tests/test_load_plan_sequence_blockers.py::test_sequence_snapshot_excluded_review_item_creates_warning_blocker -q
```

Expected: pass after Task 2 implementation; if failures appear, adjust only the sequence service logic, not previous review decision behavior.

- [ ] **Step 4: Commit blocker behavior**

```powershell
git add src/otm_workbench/modules/load_plan/sequence.py tests/test_load_plan_sequence_blockers.py
git commit -m "feat: derive load plan sequence blockers"
```

---

### Task 4: List, Detail, Latest Snapshot Endpoints

**Files:**
- Modify: `src/otm_workbench/modules/load_plan/routes.py`
- Modify: `tests/test_load_plan_sequence_blockers.py`

- [ ] **Step 1: Add failing route tests**

Append to `tests/test_load_plan_sequence_blockers.py`:

```python
def test_sequence_snapshot_list_detail_and_latest_endpoints(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    created = client.post(
        "/api/v1/modules/load-plan/sequence/snapshots",
        json={"package_id": package["id"]},
        headers=admin_header,
    )
    assert created.status_code == 200
    snapshot = created.json()

    listed = client.get("/api/v1/modules/load-plan/sequence/snapshots", headers=admin_header)
    filtered = client.get(
        "/api/v1/modules/load-plan/sequence/snapshots",
        params={"package_id": package["id"], "status": "BLOCKED"},
        headers=admin_header,
    )
    detail = client.get(
        f"/api/v1/modules/load-plan/sequence/snapshots/{snapshot['id']}",
        headers=admin_header,
    )
    latest = client.get(
        "/api/v1/modules/load-plan/sequence",
        params={"package_id": package["id"]},
        headers=admin_header,
    )

    assert listed.status_code == 200
    assert filtered.status_code == 200
    assert detail.status_code == 200
    assert latest.status_code == 200
    assert listed.json()["total"] == 1
    assert filtered.json()["items"][0]["id"] == snapshot["id"]
    assert detail.json()["id"] == snapshot["id"]
    assert latest.json()["id"] == snapshot["id"]


def test_sequence_latest_endpoint_rejects_missing_snapshot(client, admin_header):
    response = client.get(
        "/api/v1/modules/load-plan/sequence",
        params={"package_id": "missing_package"},
        headers=admin_header,
    )

    assert response.status_code == 404


def test_sequence_snapshot_detail_rejects_missing_snapshot(client, admin_header):
    response = client.get(
        "/api/v1/modules/load-plan/sequence/snapshots/missing_snapshot",
        headers=admin_header,
    )

    assert response.status_code == 404
```

- [ ] **Step 2: Implement list/detail/latest routes**

Modify `src/otm_workbench/modules/load_plan/routes.py` and add these routes before `/review-queue/{item_id}`:

```python
@router.get("/sequence/snapshots")
def list_sequence_snapshots(
    package_id: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    query = db.query(LoadPlanSequenceSnapshot)
    if package_id:
        query = query.filter(LoadPlanSequenceSnapshot.package_id == package_id)
    if status:
        query = query.filter(LoadPlanSequenceSnapshot.status == status)
    snapshots = query.order_by(LoadPlanSequenceSnapshot.generated_at.desc()).all()
    return PageResponse(items=[serialize_sequence_snapshot(snapshot) for snapshot in snapshots], total=len(snapshots))


@router.get("/sequence/snapshots/{snapshot_id}")
def get_sequence_snapshot(
    snapshot_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    snapshot = db.query(LoadPlanSequenceSnapshot).filter(LoadPlanSequenceSnapshot.id == snapshot_id).first()
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Load Plan sequence snapshot not found.")
    return serialize_sequence_snapshot(snapshot)


@router.get("/sequence")
def get_latest_sequence_snapshot(
    package_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    snapshot = latest_sequence_snapshot(db, package_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Load Plan sequence snapshot not found. Generate a snapshot first.")
    return serialize_sequence_snapshot(snapshot)
```

- [ ] **Step 3: Run route tests**

Run:

```powershell
python -m pytest tests/test_load_plan_sequence_blockers.py::test_sequence_snapshot_list_detail_and_latest_endpoints tests/test_load_plan_sequence_blockers.py::test_sequence_latest_endpoint_rejects_missing_snapshot tests/test_load_plan_sequence_blockers.py::test_sequence_snapshot_detail_rejects_missing_snapshot -q
```

Expected: pass.

- [ ] **Step 4: Commit route coverage**

```powershell
git add src/otm_workbench/modules/load_plan/routes.py tests/test_load_plan_sequence_blockers.py
git commit -m "feat: expose load plan sequence snapshots"
```

---

### Task 5: Data Dictionary Edge Cases And README

**Files:**
- Modify: `tests/test_load_plan_sequence_blockers.py`
- Modify: `README.md`

- [ ] **Step 1: Add focused Data Dictionary missing-table test**

Append to `tests/test_load_plan_sequence_blockers.py`:

```python
def test_sequence_snapshot_missing_dictionary_table_creates_blocker(client, admin_header, db_session):
    batch, export, approval, package = prepare_registered_load_plan_package(client, admin_header)
    model = db_session.query(LoadPlanPackage).filter(LoadPlanPackage.id == package["id"]).one()
    model.load_sequence_json = json.dumps(
        [
            {
                "position": 1,
                "table_name": "SYNTHETIC_UNKNOWN_TABLE",
                "row_count": 1,
                "requirement_level": "OPTIONAL",
            }
        ],
        sort_keys=True,
    )
    db_session.commit()

    response = client.post(
        "/api/v1/modules/load-plan/sequence/snapshots",
        json={"package_id": package["id"]},
        headers=admin_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["sequence"][0]["dictionary_table_found"] is False
    assert "DICTIONARY_TABLE_MISSING" in [item["code"] for item in payload["blockers"]]
    assert "review_package_dependencies" in payload["summary"]["next_actions"]
```

- [ ] **Step 2: Run the Data Dictionary test**

Run:

```powershell
python -m pytest tests/test_load_plan_sequence_blockers.py::test_sequence_snapshot_missing_dictionary_table_creates_blocker -q
```

Expected: pass.

- [ ] **Step 3: Update README**

Add after the Load Plan Review Decisions paragraph in `README.md`:

```markdown
The Load Plan Sequence Blockers slice generates backend-only sequence snapshots
with client-safe blockers from package metadata, latest ZIP Analysis, review
decisions, and local OTM Data Dictionary parent-table dependencies. It does not
execute CSVUTIL, connect to OTM, transition package status, or produce cutover
readiness.
```

Extend the verification command:

```powershell
python -m pytest tests/test_reference_catalog.py tests/test_rates_dictionary.py tests/test_rates_csv_preview.py tests/test_rates_batch_approval.py tests/test_load_plan_package_intake.py tests/test_load_plan_csvutil_builder.py tests/test_load_plan_zip_analysis.py tests/test_load_plan_review_queue.py tests/test_load_plan_review_decisions.py tests/test_load_plan_sequence_blockers.py
```

- [ ] **Step 4: Run focused sequence tests and README diff**

Run:

```powershell
python -m pytest tests/test_load_plan_sequence_blockers.py -q
git diff -- README.md tests/test_load_plan_sequence_blockers.py
```

Expected: all sequence tests pass; README mentions no real client names.

- [ ] **Step 5: Commit docs and edge cases**

```powershell
git add README.md tests/test_load_plan_sequence_blockers.py
git commit -m "docs: document load plan sequence blockers"
```

---

### Task 6: Full Verification, PR, And Merge

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
- Alembic upgrades through `f2a6c8d1e9b4`.
- Ruff reports `All checks passed!`.

- [ ] **Step 2: Inspect git status**

Run:

```powershell
git status --short --branch
```

Expected:

```text
## codex/load-plan-sequence-blockers
?? OTM_RESOURCES/
```

`OTM_RESOURCES/` must remain untracked.

- [ ] **Step 3: Push branch**

```powershell
git push -u origin codex/load-plan-sequence-blockers
```

- [ ] **Step 4: Open PR**

Use GitHub connector or GitHub CLI fallback if available:

Title:

```text
Load Plan Sequence Blockers
```

Body:

```markdown
## Summary
- Add Load Plan sequence snapshot persistence and migration.
- Generate client-safe sequence blockers from package metadata, ZIP Analysis, review decisions, and local Data Dictionary parent-table dependencies.
- Add sequence snapshot create/list/detail/latest APIs without CSVUTIL execution, OTM upload, package status transition, or cutover readiness.

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
git branch -d codex/load-plan-sequence-blockers
git status --short --branch
```

Expected: `main` is current and only `OTM_RESOURCES/` is untracked.

---

## Self-Review Checklist

- Spec coverage: persistence, API, Data Dictionary dependencies, blockers, evidence/audit/event, tests, README, and exclusions are covered.
- Placeholder scan: no deferred implementation text is present; all steps include concrete files, snippets, and commands.
- Type consistency: model name `LoadPlanSequenceSnapshot`, table `load_plan_sequence_snapshots`, service functions, endpoint paths, blocker codes, and event/action names match the design spec.
- Data safety: tests and examples use `OTM1`, `DEMO`, and synthetic notes only; raw row values and review decision notes are excluded from client-safe metadata.
