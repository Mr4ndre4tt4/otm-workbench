# Workbench Assistant Saved Query Corpus Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first saved-query corpus foundation for the Workbench Assistant so the SQL Helper can store, validate, approve, and search trusted SELECT examples without using real client data or executing SQL.

**Architecture:** Extend the existing Assistant backend with saved-query SQLAlchemy models, deterministic validation in `assistant/sql_helper.py`, and API routes under `/api/v1/assistant/sql/saved-queries`. The slice stores metadata, validates SELECT-only SQL against the Data Dictionary, blocks unsafe literals during approval, and returns scoped search results; it does not extract join patterns yet.

**Tech Stack:** Python 3.13, FastAPI, Pydantic, SQLAlchemy, existing Data Dictionary services, pytest.

---

## Scope Guard

In scope:
- Saved query models for query metadata, referenced tables, and referenced columns.
- Create draft saved query.
- Approve saved query only if SQL is SELECT-only, references known tables/columns, and avoids literal client-like values.
- Retired saved queries hidden from default search.
- Search saved queries by text/table/module/status with existing scope rules.
- Data Dictionary citations in response payloads.

Out of scope:
- SQL execution.
- join pattern extraction.
- UI.
- Oracle docs lookup.
- LLM generation.
- import from arbitrary files.
- real client examples.

## File Structure

- Modify `src/otm_workbench/models.py`
  - Add `AssistantSavedQuery`, `AssistantSavedQueryTable`, and `AssistantSavedQueryColumn`.
- Create `src/otm_workbench/assistant/saved_queries.py`
  - Query validation, table/column extraction, sanitization checks, create/approve/search serializers.
- Modify `src/otm_workbench/assistant/routes.py`
  - Add request models and saved-query endpoints.
- Modify `tests/test_assistant_source_index.py`
  - Add corpus tests.
- Modify docs:
  - `docs/agent/assistant-planning/QUERY_CORPUS_STRATEGY.md`
  - `docs/agent/HANDOFF.md`
  - `docs/agent/VALIDATION_REPORT.md`

## Data Model

```python
class AssistantSavedQuery(Base, TimestampMixin):
    __tablename__ = "assistant_saved_queries"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String, index=True)
    purpose: Mapped[str] = mapped_column(Text, default="")
    sql_text: Mapped[str] = mapped_column(Text)
    module_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String, default="DRAFT", index=True)
    visibility: Mapped[str] = mapped_column(String, default="PRIVATE", index=True)
    project_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    profile_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    environment_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    domain_name: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    access_policy_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    warnings_json: Mapped[str] = mapped_column(Text, default="[]")
    created_by: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    reviewed_by: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class AssistantSavedQueryTable(Base, TimestampMixin):
    __tablename__ = "assistant_saved_query_tables"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    query_id: Mapped[str] = mapped_column(ForeignKey("assistant_saved_queries.id"), index=True)
    table_name: Mapped[str] = mapped_column(String, index=True)
    alias: Mapped[str] = mapped_column(String, default="")
    role: Mapped[str] = mapped_column(String, default="PRIMARY", index=True)


class AssistantSavedQueryColumn(Base, TimestampMixin):
    __tablename__ = "assistant_saved_query_columns"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    query_id: Mapped[str] = mapped_column(ForeignKey("assistant_saved_queries.id"), index=True)
    table_name: Mapped[str] = mapped_column(String, index=True)
    column_name: Mapped[str] = mapped_column(String, index=True)
    alias: Mapped[str] = mapped_column(String, default="")
    role: Mapped[str] = mapped_column(String, default="SELECTED", index=True)
```

## Task 1: Models And Draft Creation

**Files:**
- Modify: `src/otm_workbench/models.py`
- Create: `src/otm_workbench/assistant/saved_queries.py`
- Modify: `tests/test_assistant_source_index.py`

- [ ] **Step 1: Write failing tests**

```python
from otm_workbench.assistant.saved_queries import create_saved_query, search_saved_queries
from otm_workbench.models import AssistantSavedQuery, AssistantSavedQueryColumn, AssistantSavedQueryTable


def test_saved_query_models_and_draft_creation(db_session):
    query = create_saved_query(
        db_session,
        name="Rate geo cost lookup",
        purpose="Find rate geo cost by group.",
        sql_text="select rgc.rate_geo_cost_group_gid from rate_geo_cost rgc where rgc.rate_geo_cost_group_gid = :rate_geo_cost_group_gid",
        module_id="rates",
        visibility="PUBLIC",
        created_by="synthetic-user",
    )

    assert query.status == "DRAFT"
    assert db_session.query(AssistantSavedQuery).count() == 1
    assert db_session.query(AssistantSavedQueryTable).count() == 1
    assert db_session.query(AssistantSavedQueryColumn).count() == 1
```

- [ ] **Step 2: Verify RED**

Run: `pytest tests/test_assistant_source_index.py -k "saved_query" -v`

Expected: FAIL with import/model missing.

- [ ] **Step 3: Add models**

Add the three SQLAlchemy models from the Data Model section to `src/otm_workbench/models.py` near other Assistant models.

- [ ] **Step 4: Implement draft creation**

Create `src/otm_workbench/assistant/saved_queries.py` with:

```python
import json
import re

from sqlalchemy.orm import Session

from otm_workbench.models import AssistantSavedQuery, AssistantSavedQueryColumn, AssistantSavedQueryTable


SELECT_FROM_PATTERN = re.compile(r"\bselect\s+(.*?)\s+from\s+([a-zA-Z0-9_]+)(?:\s+([a-zA-Z0-9_]+))?", re.IGNORECASE | re.DOTALL)


def extract_single_table_references(sql_text: str) -> tuple[str, str, list[str]]:
    match = SELECT_FROM_PATTERN.search(sql_text)
    if not match:
        return "", "", []
    raw_columns = [item.strip() for item in match.group(1).split(",")]
    table_name = match.group(2).upper()
    alias = match.group(3) or ""
    columns = []
    for raw_column in raw_columns:
        column = raw_column.split()[0]
        if alias:
            column = column.replace(f"{alias}.", "", 1).replace(f"{alias.upper()}.", "", 1)
        columns.append(column.upper())
    return table_name, alias, columns


def create_saved_query(
    db: Session,
    *,
    name: str,
    purpose: str,
    sql_text: str,
    module_id: str | None = None,
    visibility: str = "PRIVATE",
    project_id: str | None = None,
    profile_id: str | None = None,
    environment_id: str | None = None,
    domain_name: str | None = None,
    access_policy_id: str | None = None,
    created_by: str | None = None,
) -> AssistantSavedQuery:
    table_name, alias, columns = extract_single_table_references(sql_text)
    query = AssistantSavedQuery(
        name=name.strip(),
        purpose=purpose.strip(),
        sql_text=sql_text.strip(),
        module_id=module_id,
        visibility=visibility.strip().upper(),
        project_id=project_id,
        profile_id=profile_id,
        environment_id=environment_id,
        domain_name=domain_name.upper() if domain_name else None,
        access_policy_id=access_policy_id,
        created_by=created_by,
        warnings_json="[]",
    )
    db.add(query)
    db.flush()
    if table_name:
        db.add(AssistantSavedQueryTable(query_id=query.id, table_name=table_name, alias=alias or "", role="PRIMARY"))
    for column in columns:
        db.add(AssistantSavedQueryColumn(query_id=query.id, table_name=table_name, column_name=column, alias=alias or "", role="SELECTED"))
    db.commit()
    db.refresh(query)
    return query
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_assistant_source_index.py -k "saved_query_models" -v`

Expected: PASS.

## Task 2: Approval Validation And Sanitization

**Files:**
- Modify: `src/otm_workbench/assistant/saved_queries.py`
- Modify: `tests/test_assistant_source_index.py`

- [ ] **Step 1: Write failing tests**

```python
from pathlib import Path

from otm_workbench.assistant.saved_queries import approve_saved_query
from otm_workbench.config import get_settings


def test_saved_query_approval_validates_dictionary_references(db_session):
    query = create_saved_query(
        db_session,
        name="Rate geo cost lookup",
        purpose="Find rate geo cost by group.",
        sql_text="select rgc.rate_geo_cost_group_gid from rate_geo_cost rgc where rgc.rate_geo_cost_group_gid = :rate_geo_cost_group_gid",
        visibility="PUBLIC",
    )

    approved = approve_saved_query(db_session, query.id, dictionary_root=Path(get_settings().otm_data_dictionary_root), reviewed_by="reviewer")

    assert approved.status == "APPROVED"
    assert approved.reviewed_by == "reviewer"


def test_saved_query_approval_blocks_unknown_column(db_session):
    query = create_saved_query(
        db_session,
        name="Broken query",
        purpose="Broken query.",
        sql_text="select rgc.missing_column from rate_geo_cost rgc",
        visibility="PUBLIC",
    )

    approved = approve_saved_query(db_session, query.id, dictionary_root=Path(get_settings().otm_data_dictionary_root), reviewed_by="reviewer")

    assert approved.status == "DRAFT"
    assert "RATE_GEO_COST.MISSING_COLUMN was not found." in approved.warnings_json


def test_saved_query_approval_blocks_literal_values(db_session):
    query = create_saved_query(
        db_session,
        name="Unsafe literal",
        purpose="Unsafe literal.",
        sql_text="select s.shipment_gid from shipment s where s.shipment_gid = 'SYNTHETIC.REAL_LOOKING_VALUE'",
        visibility="PUBLIC",
    )

    approved = approve_saved_query(db_session, query.id, dictionary_root=Path(get_settings().otm_data_dictionary_root), reviewed_by="reviewer")

    assert approved.status == "DRAFT"
    assert "Use bind parameters instead of quoted literals." in approved.warnings_json
```

- [ ] **Step 2: Verify RED**

Run: `pytest tests/test_assistant_source_index.py -k "saved_query_approval" -v`

Expected: FAIL with `approve_saved_query` missing.

- [ ] **Step 3: Implement approval**

Append to `saved_queries.py`:

```python
from pathlib import Path

from otm_workbench.assistant.sql_helper import reject_unsafe_sql, validate_table_and_columns
from otm_workbench.models import utcnow


QUOTED_LITERAL_PATTERN = re.compile(r"=\s*'[^']+'")


def approve_saved_query(db: Session, query_id: str, *, dictionary_root: Path, reviewed_by: str) -> AssistantSavedQuery:
    query = db.get(AssistantSavedQuery, query_id)
    if query is None:
        raise ValueError("Saved query not found.")
    warnings = []
    unsafe = reject_unsafe_sql(query.sql_text)
    if unsafe:
        warnings.extend(unsafe["warnings"])
    if QUOTED_LITERAL_PATTERN.search(query.sql_text):
        warnings.append("Use bind parameters instead of quoted literals.")
    tables = db.query(AssistantSavedQueryTable).filter(AssistantSavedQueryTable.query_id == query.id).all()
    columns = db.query(AssistantSavedQueryColumn).filter(AssistantSavedQueryColumn.query_id == query.id).all()
    for table in tables:
        table_columns = [column.column_name for column in columns if column.table_name == table.table_name]
        _, table_warnings = validate_table_and_columns(dictionary_root, table.table_name, table_columns)
        warnings.extend(table_warnings)
    query.warnings_json = json.dumps(warnings, sort_keys=True)
    if warnings:
        query.status = "DRAFT"
    else:
        query.status = "APPROVED"
        query.reviewed_by = reviewed_by
        query.reviewed_at = utcnow()
    db.commit()
    db.refresh(query)
    return query
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_assistant_source_index.py -k "saved_query_approval" -v`

Expected: PASS.

## Task 3: Search And API

**Files:**
- Modify: `src/otm_workbench/assistant/saved_queries.py`
- Modify: `src/otm_workbench/assistant/routes.py`
- Modify: `tests/test_assistant_source_index.py`

- [ ] **Step 1: Write failing API/search tests**

```python
def test_saved_query_search_hides_retired_by_default(db_session):
    approved = create_saved_query(db_session, name="Approved rate lookup", purpose="Approved.", sql_text="select rgc.rate_geo_cost_group_gid from rate_geo_cost rgc", visibility="PUBLIC")
    retired = create_saved_query(db_session, name="Retired rate lookup", purpose="Retired.", sql_text="select rgc.rate_geo_cost_group_gid from rate_geo_cost rgc", visibility="PUBLIC")
    approved.status = "APPROVED"
    retired.status = "RETIRED"
    db_session.commit()

    results = search_saved_queries(db_session, query_text="rate lookup", allowed_domains=["PUBLIC"])

    assert [item["name"] for item in results] == ["Approved rate lookup"]


def test_assistant_saved_query_create_and_search_api(client, admin_header):
    created = client.post(
        "/api/v1/assistant/sql/saved-queries",
        headers=admin_header,
        json={
            "name": "Rate geo cost lookup",
            "purpose": "Find rate geo cost by group.",
            "sql_text": "select rgc.rate_geo_cost_group_gid from rate_geo_cost rgc where rgc.rate_geo_cost_group_gid = :rate_geo_cost_group_gid",
            "module_id": "rates",
            "visibility": "PUBLIC",
        },
    )
    approved = client.post(f"/api/v1/assistant/sql/saved-queries/{created.json()['id']}/approve", headers=admin_header)
    search = client.get("/api/v1/assistant/sql/saved-queries?query=rate+geo", headers=admin_header)

    assert created.status_code == 201
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"
    assert search.status_code == 200
    assert search.json()["total"] == 1
```

- [ ] **Step 2: Verify RED**

Run: `pytest tests/test_assistant_source_index.py -k "saved_query_search or saved_query_create" -v`

Expected: FAIL with missing API/search.

- [ ] **Step 3: Implement search serializer**

Append to `saved_queries.py`:

```python
def serialize_saved_query(query: AssistantSavedQuery) -> dict[str, object]:
    return {
        "id": query.id,
        "name": query.name,
        "purpose": query.purpose,
        "module_id": query.module_id,
        "status": query.status,
        "visibility": query.visibility,
        "domain_name": query.domain_name,
        "warnings": json.loads(query.warnings_json or "[]"),
    }


def search_saved_queries(db: Session, *, query_text: str, allowed_domains: list[str], include_retired: bool = False) -> list[dict[str, object]]:
    normalized = query_text.strip().lower()
    query = db.query(AssistantSavedQuery)
    if not include_retired:
        query = query.filter(AssistantSavedQuery.status != "RETIRED")
    if "*" not in allowed_domains:
        query = query.filter(
            (AssistantSavedQuery.visibility == "PUBLIC")
            | (AssistantSavedQuery.domain_name.in_([domain.upper() for domain in allowed_domains]))
        )
    rows = query.order_by(AssistantSavedQuery.updated_at.desc()).all()
    items = []
    for row in rows:
        haystack = f"{row.name} {row.purpose} {row.sql_text} {row.module_id or ''}".lower()
        if normalized and normalized not in haystack:
            continue
        if row.status != "APPROVED":
            continue
        items.append(serialize_saved_query(row))
    return items
```

- [ ] **Step 4: Implement API endpoints**

Modify `routes.py` imports:

```python
from otm_workbench.assistant.saved_queries import approve_saved_query, create_saved_query, search_saved_queries
```

Add request model:

```python
class SavedQueryCreateRequest(BaseModel):
    name: str
    purpose: str
    sql_text: str
    module_id: str | None = None
    visibility: str = "PRIVATE"
    project_id: str | None = None
    profile_id: str | None = None
    environment_id: str | None = None
    domain_name: str | None = None
    access_policy_id: str | None = None
```

Add endpoints:

```python
@router.post("/sql/saved-queries", status_code=status.HTTP_201_CREATED)
def create_sql_saved_query(request: SavedQueryCreateRequest, db: Session = Depends(get_db), user: User = Depends(require_user)):
    context = active_context_for_user(db, user)
    query = create_saved_query(
        db,
        name=request.name,
        purpose=request.purpose,
        sql_text=request.sql_text,
        module_id=request.module_id,
        visibility=request.visibility,
        project_id=request.project_id or (context.project_id if context else None),
        profile_id=request.profile_id or (context.profile_id if context else None),
        environment_id=request.environment_id or (context.environment_id if context else None),
        domain_name=request.domain_name or (context.domain_name if context else None),
        access_policy_id=request.access_policy_id,
        created_by=user.id,
    )
    return serialize_saved_query(query)


@router.post("/sql/saved-queries/{query_id}/approve")
def approve_sql_saved_query(query_id: str, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    query = approve_saved_query(db, query_id, dictionary_root=dictionary_root(), reviewed_by=user.id)
    return serialize_saved_query(query)


@router.get("/sql/saved-queries")
def list_sql_saved_queries(query: str = "", db: Session = Depends(get_db), user: User = Depends(require_user)):
    context = active_context_for_user(db, user)
    allowed_domains = allowed_domains_for_context(
        context.domain_name if context else None,
        user.is_admin or bool(context and context.can_view_all_domains),
    )
    items = search_saved_queries(db, query_text=query, allowed_domains=allowed_domains)
    return PageResponse(items=items, total=len(items), page=1, page_size=len(items))
```

- [ ] **Step 5: Run API/search tests**

Run: `pytest tests/test_assistant_source_index.py -k "saved_query" -v`

Expected: PASS.

## Task 4: Validation And Documentation

**Files:**
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

Run: `rg -n "T[O]DO|T[B]D|place[Hh]older|implement late[r]|fill i[n]" src/otm_workbench/assistant tests/test_assistant_source_index.py docs/agent/assistant-planning docs/superpowers/plans/2026-05-28-workbench-assistant-saved-query-corpus-foundation.md`

Expected: no output.

- [ ] **Step 5: Update docs**

Add implemented foundation notes:

```markdown
## Implemented Foundation

The first saved query corpus slice supports:

- draft saved query creation;
- approval only for SELECT-only, Data Dictionary-backed examples;
- rejection of quoted literal filters during approval;
- search of approved queries only by default;
- retired queries hidden from default search;
- scoped query visibility using the Assistant context rules.

Join pattern extraction remains outside this slice.
```

## Self-Review

Spec coverage:
- Adds a local query corpus without AI, web, or SQL execution.
- Keeps approved examples SELECT-only and Data Dictionary-backed.
- Blocks quoted literal filters during approval to avoid real client values.
- Keeps retired queries out of default search.
- Defers join extraction until after approved query corpus exists.

Risks:
- The initial SQL reference extractor is intentionally single-table and simple.
- Approval should not be treated as DBA review for joins until join-pattern validation exists.
