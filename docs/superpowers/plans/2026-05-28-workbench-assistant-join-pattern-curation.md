# Workbench Assistant Join Pattern Curation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add reviewed join-pattern curation for the Assistant SQL Helper so approved table relationships can be stored, validated, searched, and cited before any join draft generation is allowed.

**Architecture:** Add an `AssistantJoinPattern` model and a focused `assistant/join_patterns.py` service. Join patterns are explicitly created and approved through backend routes, validated against the OTM Data Dictionary, optionally linked to an approved saved query, and searchable by table/module. This slice does not yet generate joined SQL; it creates the safe relationship library needed for that later step.

**Tech Stack:** Python 3.13, FastAPI, Pydantic, SQLAlchemy, existing Data Dictionary validation, pytest.

---

## Scope Guard

In scope:
- Store curated join patterns.
- Validate left/right table and column references against the Data Dictionary.
- Require approved saved-query source when `source_type="SAVED_QUERY"`.
- Approve valid patterns and keep invalid patterns in `DRAFT` with warnings.
- Search approved, non-retired patterns by table/name/module.
- Expose backend-only API endpoints under `/api/v1/assistant/sql/join-patterns`.

Out of scope:
- Automatic join extraction from arbitrary SQL.
- SQL join draft generation.
- Multi-join planning.
- UI.
- SQL execution.
- LLM or web lookup.

## File Structure

- Modify `src/otm_workbench/models.py`
  - Add `AssistantJoinPattern`.
- Create `src/otm_workbench/assistant/join_patterns.py`
  - Create, approve, validate, serialize, and search join patterns.
- Modify `src/otm_workbench/assistant/routes.py`
  - Add request models and join-pattern endpoints.
- Modify `tests/test_assistant_source_index.py`
  - Add join-pattern tests.
- Modify docs:
  - `docs/agent/assistant-planning/SQL_HELPER_DESIGN.md`
  - `docs/agent/assistant-planning/QUERY_CORPUS_STRATEGY.md`
  - `docs/agent/HANDOFF.md`
  - `docs/agent/VALIDATION_REPORT.md`

## Data Model

```python
class AssistantJoinPattern(Base, TimestampMixin):
    __tablename__ = "assistant_join_patterns"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String, index=True)
    module_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    left_table: Mapped[str] = mapped_column(String, index=True)
    left_column: Mapped[str] = mapped_column(String, index=True)
    right_table: Mapped[str] = mapped_column(String, index=True)
    right_column: Mapped[str] = mapped_column(String, index=True)
    join_type: Mapped[str] = mapped_column(String, default="INNER", index=True)
    business_meaning: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[str] = mapped_column(String, default="LOW", index=True)
    status: Mapped[str] = mapped_column(String, default="DRAFT", index=True)
    source_type: Mapped[str] = mapped_column(String, default="MANUAL", index=True)
    source_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    warnings_json: Mapped[str] = mapped_column(Text, default="[]")
    created_by: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    reviewed_by: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

## Task 1: Model And Draft Creation

**Files:**
- Modify: `src/otm_workbench/models.py`
- Create: `src/otm_workbench/assistant/join_patterns.py`
- Modify: `tests/test_assistant_source_index.py`

- [ ] **Step 1: Write failing tests**

```python
from otm_workbench.assistant.join_patterns import create_join_pattern
from otm_workbench.models import AssistantJoinPattern


def test_join_pattern_model_and_draft_creation(db_session):
    pattern = create_join_pattern(
        db_session,
        name="Shipment to shipment stop",
        left_table="SHIPMENT",
        left_column="SHIPMENT_GID",
        right_table="SHIPMENT_STOP",
        right_column="SHIPMENT_GID",
        join_type="INNER",
        business_meaning="Shipment header to stops.",
        module_id="order_release_generator",
        created_by="synthetic-user",
    )

    assert pattern.status == "DRAFT"
    assert pattern.confidence == "LOW"
    assert db_session.query(AssistantJoinPattern).count() == 1
```

- [ ] **Step 2: Verify RED**

Run: `pytest tests/test_assistant_source_index.py -k "join_pattern" -v`

Expected: FAIL with missing module/model.

- [ ] **Step 3: Add model**

Add `AssistantJoinPattern` from the Data Model section to `src/otm_workbench/models.py` next to other Assistant models.

- [ ] **Step 4: Implement draft creation**

Create `src/otm_workbench/assistant/join_patterns.py`:

```python
import json
from pathlib import Path

from sqlalchemy import or_
from sqlalchemy.orm import Session

from otm_workbench.assistant.sql_helper import validate_table_and_columns
from otm_workbench.models import AssistantJoinPattern, AssistantSavedQuery, utcnow


def normalize_join_type(value: str) -> str:
    normalized = value.strip().upper()
    return normalized if normalized in {"INNER", "LEFT", "EXISTS"} else "INNER"


def create_join_pattern(
    db: Session,
    *,
    name: str,
    left_table: str,
    left_column: str,
    right_table: str,
    right_column: str,
    join_type: str = "INNER",
    business_meaning: str = "",
    module_id: str | None = None,
    source_type: str = "MANUAL",
    source_id: str | None = None,
    created_by: str | None = None,
) -> AssistantJoinPattern:
    pattern = AssistantJoinPattern(
        name=name.strip(),
        module_id=module_id,
        left_table=left_table.strip().upper(),
        left_column=left_column.strip().upper(),
        right_table=right_table.strip().upper(),
        right_column=right_column.strip().upper(),
        join_type=normalize_join_type(join_type),
        business_meaning=business_meaning.strip(),
        source_type=source_type.strip().upper(),
        source_id=source_id,
        created_by=created_by,
        warnings_json="[]",
    )
    db.add(pattern)
    db.commit()
    db.refresh(pattern)
    return pattern
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_assistant_source_index.py -k "join_pattern_model" -v`

Expected: PASS.

## Task 2: Approval Validation

**Files:**
- Modify: `src/otm_workbench/assistant/join_patterns.py`
- Modify: `tests/test_assistant_source_index.py`

- [ ] **Step 1: Write failing tests**

```python
from otm_workbench.assistant.join_patterns import approve_join_pattern


def test_join_pattern_approval_validates_dictionary_references(db_session):
    pattern = create_join_pattern(
        db_session,
        name="Shipment to shipment stop",
        left_table="SHIPMENT",
        left_column="SHIPMENT_GID",
        right_table="SHIPMENT_STOP",
        right_column="SHIPMENT_GID",
        business_meaning="Shipment header to stops.",
    )

    approved = approve_join_pattern(db_session, pattern.id, dictionary_root=dictionary_root(), reviewed_by="reviewer")

    assert approved.status == "APPROVED"
    assert approved.confidence == "HIGH"
    assert approved.reviewed_by == "reviewer"


def test_join_pattern_approval_blocks_unknown_column(db_session):
    pattern = create_join_pattern(
        db_session,
        name="Broken join",
        left_table="SHIPMENT",
        left_column="MISSING_COLUMN",
        right_table="SHIPMENT_STOP",
        right_column="SHIPMENT_GID",
    )

    approved = approve_join_pattern(db_session, pattern.id, dictionary_root=dictionary_root(), reviewed_by="reviewer")

    assert approved.status == "DRAFT"
    assert "SHIPMENT.MISSING_COLUMN was not found." in approved.warnings_json


def test_join_pattern_saved_query_source_requires_approved_query(db_session):
    from otm_workbench.assistant.saved_queries import create_saved_query

    saved_query = create_saved_query(
        db_session,
        name="Draft shipment stop query",
        purpose="Draft source.",
        sql_text="select s.shipment_gid from shipment s",
        visibility="PUBLIC",
    )
    pattern = create_join_pattern(
        db_session,
        name="Shipment to stop from draft",
        left_table="SHIPMENT",
        left_column="SHIPMENT_GID",
        right_table="SHIPMENT_STOP",
        right_column="SHIPMENT_GID",
        source_type="SAVED_QUERY",
        source_id=saved_query.id,
    )

    approved = approve_join_pattern(db_session, pattern.id, dictionary_root=dictionary_root(), reviewed_by="reviewer")

    assert approved.status == "DRAFT"
    assert "Saved query source must be approved before it can validate a join pattern." in approved.warnings_json
```

- [ ] **Step 2: Verify RED**

Run: `pytest tests/test_assistant_source_index.py -k "join_pattern_approval" -v`

Expected: FAIL with missing `approve_join_pattern`.

- [ ] **Step 3: Implement approval**

Append to `join_patterns.py`:

```python
def validate_join_pattern(db: Session, pattern: AssistantJoinPattern, dictionary_root: Path) -> list[str]:
    warnings = []
    _, left_warnings = validate_table_and_columns(dictionary_root, pattern.left_table, [pattern.left_column])
    _, right_warnings = validate_table_and_columns(dictionary_root, pattern.right_table, [pattern.right_column])
    warnings.extend(left_warnings)
    warnings.extend(right_warnings)
    if pattern.source_type == "SAVED_QUERY":
        saved_query = db.get(AssistantSavedQuery, pattern.source_id)
        if saved_query is None or saved_query.status != "APPROVED":
            warnings.append("Saved query source must be approved before it can validate a join pattern.")
    return warnings


def approve_join_pattern(db: Session, pattern_id: str, *, dictionary_root: Path, reviewed_by: str) -> AssistantJoinPattern:
    pattern = db.get(AssistantJoinPattern, pattern_id)
    if pattern is None:
        raise ValueError("Join pattern not found.")
    warnings = validate_join_pattern(db, pattern, dictionary_root)
    pattern.warnings_json = json.dumps(warnings, sort_keys=True)
    if warnings:
        pattern.status = "DRAFT"
        pattern.confidence = "LOW"
    else:
        pattern.status = "APPROVED"
        pattern.confidence = "HIGH"
        pattern.reviewed_by = reviewed_by
        pattern.reviewed_at = utcnow()
    db.commit()
    db.refresh(pattern)
    return pattern
```

- [ ] **Step 4: Run approval tests**

Run: `pytest tests/test_assistant_source_index.py -k "join_pattern_approval" -v`

Expected: PASS.

## Task 3: Search And API

**Files:**
- Modify: `src/otm_workbench/assistant/join_patterns.py`
- Modify: `src/otm_workbench/assistant/routes.py`
- Modify: `tests/test_assistant_source_index.py`

- [ ] **Step 1: Write failing API/search tests**

```python
def test_join_pattern_search_returns_only_approved_by_default(db_session):
    approved = create_join_pattern(
        db_session,
        name="Approved shipment stop join",
        left_table="SHIPMENT",
        left_column="SHIPMENT_GID",
        right_table="SHIPMENT_STOP",
        right_column="SHIPMENT_GID",
    )
    draft = create_join_pattern(
        db_session,
        name="Draft shipment stop join",
        left_table="SHIPMENT",
        left_column="SHIPMENT_GID",
        right_table="SHIPMENT_STOP",
        right_column="SHIPMENT_GID",
    )
    approved.status = "APPROVED"
    approved.confidence = "HIGH"
    db_session.commit()

    results = search_join_patterns(db_session, query_text="shipment stop")

    assert [item["name"] for item in results] == ["Approved shipment stop join"]


def test_assistant_join_pattern_create_approve_and_search_api(client, admin_header):
    created = client.post(
        "/api/v1/assistant/sql/join-patterns",
        headers=admin_header,
        json={
            "name": "Shipment to shipment stop",
            "left_table": "SHIPMENT",
            "left_column": "SHIPMENT_GID",
            "right_table": "SHIPMENT_STOP",
            "right_column": "SHIPMENT_GID",
            "join_type": "INNER",
            "business_meaning": "Shipment header to stops.",
            "module_id": "order_release_generator",
        },
    )
    approved = client.post(f"/api/v1/assistant/sql/join-patterns/{created.json().get('id', 'missing')}/approve", headers=admin_header)
    search = client.get("/api/v1/assistant/sql/join-patterns?query=shipment+stop", headers=admin_header)

    assert created.status_code == 201
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"
    assert search.status_code == 200
    assert search.json()["total"] == 1
```

- [ ] **Step 2: Verify RED**

Run: `pytest tests/test_assistant_source_index.py -k "join_pattern_search or join_pattern_create" -v`

Expected: FAIL with missing search/API.

- [ ] **Step 3: Implement serializer/search**

Append to `join_patterns.py`:

```python
def serialize_join_pattern(pattern: AssistantJoinPattern) -> dict[str, object]:
    return {
        "id": pattern.id,
        "name": pattern.name,
        "module_id": pattern.module_id,
        "left_table": pattern.left_table,
        "left_column": pattern.left_column,
        "right_table": pattern.right_table,
        "right_column": pattern.right_column,
        "join_type": pattern.join_type,
        "business_meaning": pattern.business_meaning,
        "confidence": pattern.confidence,
        "status": pattern.status,
        "source_type": pattern.source_type,
        "source_id": pattern.source_id,
        "warnings": json.loads(pattern.warnings_json or "[]"),
    }


def search_join_patterns(db: Session, *, query_text: str = "", table_name: str | None = None, include_draft: bool = False) -> list[dict[str, object]]:
    query = db.query(AssistantJoinPattern)
    if not include_draft:
        query = query.filter(AssistantJoinPattern.status == "APPROVED")
    if table_name:
        normalized_table = table_name.upper()
        query = query.filter(or_(AssistantJoinPattern.left_table == normalized_table, AssistantJoinPattern.right_table == normalized_table))
    normalized = query_text.strip().lower()
    rows = query.order_by(AssistantJoinPattern.updated_at.desc()).all()
    items = []
    for row in rows:
        haystack = f"{row.name} {row.business_meaning} {row.left_table} {row.right_table} {row.module_id or ''}".lower()
        if normalized and normalized not in haystack:
            continue
        items.append(serialize_join_pattern(row))
    return items
```

- [ ] **Step 4: Implement API**

Modify `routes.py` imports:

```python
from otm_workbench.assistant.join_patterns import approve_join_pattern, create_join_pattern, search_join_patterns, serialize_join_pattern
```

Add request model:

```python
class JoinPatternCreateRequest(BaseModel):
    name: str
    left_table: str
    left_column: str
    right_table: str
    right_column: str
    join_type: str = "INNER"
    business_meaning: str = ""
    module_id: str | None = None
    source_type: str = "MANUAL"
    source_id: str | None = None
```

Add endpoints:

```python
@router.post("/sql/join-patterns", status_code=status.HTTP_201_CREATED)
def create_sql_join_pattern(request: JoinPatternCreateRequest, db: Session = Depends(get_db), user: User = Depends(require_user)):
    pattern = create_join_pattern(
        db,
        name=request.name,
        left_table=request.left_table,
        left_column=request.left_column,
        right_table=request.right_table,
        right_column=request.right_column,
        join_type=request.join_type,
        business_meaning=request.business_meaning,
        module_id=request.module_id,
        source_type=request.source_type,
        source_id=request.source_id,
        created_by=user.id,
    )
    return serialize_join_pattern(pattern)


@router.post("/sql/join-patterns/{pattern_id}/approve")
def approve_sql_join_pattern(pattern_id: str, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    pattern = approve_join_pattern(db, pattern_id, dictionary_root=dictionary_root(), reviewed_by=user.id)
    return serialize_join_pattern(pattern)


@router.get("/sql/join-patterns")
def list_sql_join_patterns(query: str = "", table_name: str | None = None, db: Session = Depends(get_db), user: User = Depends(require_user)):
    items = search_join_patterns(db, query_text=query, table_name=table_name)
    return PageResponse(items=items, total=len(items), page=1, page_size=len(items))
```

- [ ] **Step 5: Run search/API tests**

Run: `pytest tests/test_assistant_source_index.py -k "join_pattern" -v`

Expected: PASS.

## Task 4: Validation And Documentation

**Files:**
- Modify: `docs/agent/assistant-planning/SQL_HELPER_DESIGN.md`
- Modify: `docs/agent/assistant-planning/QUERY_CORPUS_STRATEGY.md`
- Modify: `docs/agent/HANDOFF.md`
- Modify: `docs/agent/VALIDATION_REPORT.md`

- [ ] **Step 1: Run Assistant suite**

Run: `pytest tests/test_assistant_source_index.py -v`

Expected: PASS.

- [ ] **Step 2: Run navigation regression**

Run: `pytest tests/test_modules_navigation.py::test_assistant_is_not_added_to_main_navigation -v`

Expected: PASS.

- [ ] **Step 3: Run Catalog smoke**

Run: `pytest tests/test_catalog_core.py -v`

Expected: PASS.

- [ ] **Step 4: Scan for incompleteness markers**

Run: `rg -n "T[O]DO|T[B]D|place[Hh]older|implement late[r]|fill i[n]" src/otm_workbench/assistant tests/test_assistant_source_index.py docs/agent/assistant-planning docs/superpowers/plans/2026-05-28-workbench-assistant-join-pattern-curation.md`

Expected: no output.

- [ ] **Step 5: Update docs**

Add implemented notes:

```markdown
## Implemented Join Pattern Foundation

The join-pattern curation slice supports:

- draft join-pattern creation;
- approval only when both sides resolve through the Data Dictionary;
- optional approved saved-query source validation;
- search of approved join patterns by text/table;
- backend-only APIs for create, approve, and list.

Join draft generation remains outside this slice.
```

## Self-Review

Spec coverage:
- Keeps join patterns explicit and reviewed.
- Uses the Data Dictionary as table/column truth.
- Prevents draft saved queries from validating join patterns.
- Does not generate joined SQL yet.
- Keeps UI and SQL execution out of scope.

Risk:
- This does not prove a business join is semantically correct; it proves the referenced tables/columns exist and records a reviewed relationship. Real semantic approval remains a human/DBA responsibility.
