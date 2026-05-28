# Workbench Assistant SQL Helper Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first local, deterministic SQL Helper backend slice for the Workbench Assistant: SELECT-only safety checks, Data Dictionary table/column validation, pasted SELECT explanation, and a single-table query draft response.

**Architecture:** Add SQL-helper services under `src/otm_workbench/assistant/` and expose narrow FastAPI routes under `/api/v1/assistant/sql`. The helper will not use an LLM, will not execute SQL, and will not draft joins yet; every accepted draft or explanation must cite Data Dictionary-backed tables and columns.

**Tech Stack:** Python 3.13, FastAPI, Pydantic, SQLAlchemy session dependency, existing Catalog/Data Dictionary services, pytest.

---

## Scope Guard

In scope:
- Reject unsafe SQL mutation/DDL requests.
- Validate table names through the local OTM Data Dictionary.
- Validate requested columns through the local OTM Data Dictionary.
- Explain simple pasted `SELECT ... FROM ... WHERE ...` SQL by identifying known/unknown tables and columns.
- Draft a single-table parameterized SELECT when the table and columns are explicit and valid.
- Return structured `sql_draft`, `blocked`, or `clarification` payloads.

Out of scope:
- SQL execution.
- Joins.
- saved query library persistence.
- AI/LLM reasoning.
- Oracle web lookup.
- UI rendering.
- Client-specific SQL examples.

## File Structure

- Create `src/otm_workbench/assistant/sql_helper.py`
  - Deterministic parser helpers, unsafe intent detection, table/column validation, SQL explanation, single-table draft builder.
- Modify `src/otm_workbench/assistant/routes.py`
  - Add request/response models and `/sql/explain` plus `/sql/draft` endpoints.
- Modify `tests/test_assistant_source_index.py`
  - Add SQL helper API/service tests, keeping this Assistant foundation suite together for now.
- Modify `docs/agent/assistant-planning/SQL_HELPER_DESIGN.md`
  - Mark implemented foundation boundaries after code lands.
- Modify `docs/agent/HANDOFF.md` and `docs/agent/VALIDATION_REPORT.md`
  - Record validation.

## Response Shape

Blocked unsafe request:

```json
{
  "answer_type": "blocked",
  "summary": "Only SELECT drafts are supported.",
  "confidence": "high",
  "source_mode": "none",
  "cost_level": "local",
  "warnings": ["Mutation and DDL SQL are not supported by the Assistant SQL Helper."]
}
```

Single-table draft:

```json
{
  "answer_type": "sql_draft",
  "summary": "Draft SELECT for RATE_GEO_COST.",
  "confidence": "high",
  "source_mode": "generated_draft",
  "cost_level": "local",
  "block": {
    "type": "sql_draft",
    "purpose": "Find rate geo cost by GID.",
    "sql": "select rgc.RATE_GEO_COST_GROUP_GID from RATE_GEO_COST rgc where rgc.RATE_GEO_COST_GROUP_GID = :rate_geo_cost_group_gid",
    "parameters": [{"name": "rate_geo_cost_group_gid", "description": "Filter for RATE_GEO_COST.RATE_GEO_COST_GROUP_GID"}],
    "tables": ["RATE_GEO_COST"],
    "columns": ["RATE_GEO_COST.RATE_GEO_COST_GROUP_GID"],
    "assumptions": [],
    "warnings": []
  },
  "sources": [{"source_type": "data_dictionary", "title": "RATE_GEO_COST"}]
}
```

## Task 1: SQL Helper Service Safety And Validation

**Files:**
- Create: `src/otm_workbench/assistant/sql_helper.py`
- Modify: `tests/test_assistant_source_index.py`

- [ ] **Step 1: Write failing service tests**

```python
from pathlib import Path

from otm_workbench.assistant.sql_helper import (
    draft_single_table_select,
    explain_select_sql,
    reject_unsafe_sql,
)
from otm_workbench.config import get_settings


def dictionary_root() -> Path:
    return Path(get_settings().otm_data_dictionary_root)


def test_sql_helper_rejects_mutation_sql():
    payload = reject_unsafe_sql("delete from shipment where shipment_gid = :gid")

    assert payload["answer_type"] == "blocked"
    assert payload["confidence"] == "high"
    assert "Only SELECT" in payload["summary"]


def test_sql_helper_drafts_single_table_select_from_dictionary():
    payload = draft_single_table_select(
        dictionary_root(),
        table_name="RATE_GEO_COST",
        columns=["RATE_GEO_COST_GROUP_GID"],
        filter_column="RATE_GEO_COST_GROUP_GID",
        purpose="Find rate geo cost by group.",
    )

    assert payload["answer_type"] == "sql_draft"
    assert payload["confidence"] == "high"
    assert "from RATE_GEO_COST rgc" in payload["block"]["sql"]
    assert ":rate_geo_cost_group_gid" in payload["block"]["sql"]
    assert payload["block"]["tables"] == ["RATE_GEO_COST"]
    assert payload["block"]["columns"] == ["RATE_GEO_COST.RATE_GEO_COST_GROUP_GID"]
    assert payload["sources"][0]["source_type"] == "data_dictionary"


def test_sql_helper_blocks_unknown_column():
    payload = draft_single_table_select(
        dictionary_root(),
        table_name="RATE_GEO_COST",
        columns=["MISSING_COLUMN"],
        filter_column="RATE_GEO_COST_GROUP_GID",
        purpose="Find rate geo cost.",
    )

    assert payload["answer_type"] == "blocked"
    assert payload["summary"] == "One or more requested columns are not in the local Data Dictionary."
    assert payload["warnings"] == ["RATE_GEO_COST.MISSING_COLUMN was not found."]


def test_sql_helper_explains_select_and_flags_unknown_references():
    payload = explain_select_sql(
        dictionary_root(),
        "select rgc.rate_geo_cost_group_gid, rgc.missing_column from rate_geo_cost rgc where rgc.rate_geo_cost_group_gid = :gid",
    )

    assert payload["answer_type"] == "sql_draft"
    assert payload["block"]["tables"] == ["RATE_GEO_COST"]
    assert "RATE_GEO_COST.RATE_GEO_COST_GROUP_GID" in payload["block"]["columns"]
    assert "RATE_GEO_COST.MISSING_COLUMN was not found." in payload["block"]["warnings"]
    assert payload["confidence"] == "medium"
```

- [ ] **Step 2: Run tests to verify RED**

Run: `pytest tests/test_assistant_source_index.py -k "sql_helper" -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'otm_workbench.assistant.sql_helper'`.

- [ ] **Step 3: Implement service helpers**

Create `src/otm_workbench/assistant/sql_helper.py`:

```python
from pathlib import Path
import re

from otm_workbench.catalog.services import safe_load_table

UNSAFE_SQL_PATTERN = re.compile(r"\b(update|delete|insert|merge|drop|alter|truncate|create|grant|revoke)\b", re.IGNORECASE)


def blocked_response(summary: str, warnings: list[str]) -> dict[str, object]:
    return {
        "answer_type": "blocked",
        "summary": summary,
        "confidence": "high",
        "source_mode": "none",
        "cost_level": "local",
        "warnings": warnings,
    }


def reject_unsafe_sql(sql_text: str) -> dict[str, object] | None:
    if UNSAFE_SQL_PATTERN.search(sql_text):
        return blocked_response(
            "Only SELECT drafts are supported.",
            ["Mutation and DDL SQL are not supported by the Assistant SQL Helper."],
        )
    return None


def normalize_identifier(value: str) -> str:
    return value.strip().upper()


def parameter_name(column_name: str) -> str:
    return column_name.strip().lower()


def alias_for_table(table_name: str) -> str:
    parts = [part for part in table_name.lower().split("_") if part]
    return "".join(part[0] for part in parts)[:4] or "t"


def data_dictionary_source(table_name: str) -> dict[str, object]:
    return {
        "source_type": "data_dictionary",
        "title": table_name,
        "source_mode": "indexed",
        "confidence": "high",
    }


def validate_table_and_columns(dictionary_root: Path, table_name: str, columns: list[str]) -> tuple[object | None, list[str]]:
    normalized_table = normalize_identifier(table_name)
    definition = safe_load_table(dictionary_root, normalized_table)
    if definition is None:
        return None, [f"{normalized_table} was not found in the local Data Dictionary."]
    warnings = []
    for column in columns:
        normalized_column = normalize_identifier(column)
        if normalized_column not in definition.columns:
            warnings.append(f"{normalized_table}.{normalized_column} was not found.")
    return definition, warnings


def draft_single_table_select(
    dictionary_root: Path,
    *,
    table_name: str,
    columns: list[str],
    filter_column: str,
    purpose: str,
) -> dict[str, object]:
    normalized_table = normalize_identifier(table_name)
    normalized_columns = [normalize_identifier(column) for column in columns]
    normalized_filter = normalize_identifier(filter_column)
    definition, warnings = validate_table_and_columns(dictionary_root, normalized_table, normalized_columns + [normalized_filter])
    if definition is None:
        return blocked_response("Requested table was not found in the local Data Dictionary.", warnings)
    if warnings:
        return blocked_response("One or more requested columns are not in the local Data Dictionary.", warnings)
    alias = alias_for_table(normalized_table)
    selected = ", ".join(f"{alias}.{column}" for column in normalized_columns)
    bind = parameter_name(normalized_filter)
    sql = f"select {selected} from {normalized_table} {alias} where {alias}.{normalized_filter} = :{bind}"
    return {
        "answer_type": "sql_draft",
        "summary": f"Draft SELECT for {normalized_table}.",
        "confidence": "high",
        "source_mode": "generated_draft",
        "cost_level": "local",
        "block": {
            "type": "sql_draft",
            "purpose": purpose,
            "sql": sql,
            "parameters": [{"name": bind, "description": f"Filter for {normalized_table}.{normalized_filter}"}],
            "tables": [normalized_table],
            "columns": [f"{normalized_table}.{column}" for column in normalized_columns],
            "assumptions": [],
            "warnings": [],
        },
        "sources": [data_dictionary_source(normalized_table)],
    }


def explain_select_sql(dictionary_root: Path, sql_text: str) -> dict[str, object]:
    unsafe = reject_unsafe_sql(sql_text)
    if unsafe:
        return unsafe
    from_match = re.search(r"\bfrom\s+([a-zA-Z0-9_]+)(?:\s+([a-zA-Z0-9_]+))?", sql_text, flags=re.IGNORECASE)
    if not from_match:
        return blocked_response("I could not identify a FROM table in the SELECT.", ["Add an explicit FROM table."])
    table_name = normalize_identifier(from_match.group(1))
    alias = from_match.group(2) or alias_for_table(table_name)
    select_match = re.search(r"\bselect\s+(.*?)\s+from\b", sql_text, flags=re.IGNORECASE | re.DOTALL)
    raw_columns = [] if not select_match else [item.strip() for item in select_match.group(1).split(",")]
    columns = []
    for raw_column in raw_columns:
        cleaned = raw_column.split()[0]
        cleaned = cleaned.replace(f"{alias}.", "", 1).replace(f"{alias.upper()}.", "", 1)
        columns.append(normalize_identifier(cleaned))
    definition, warnings = validate_table_and_columns(dictionary_root, table_name, columns)
    if definition is None:
        return blocked_response("Requested table was not found in the local Data Dictionary.", warnings)
    known_columns = [f"{table_name}.{column}" for column in columns if column in definition.columns]
    return {
        "answer_type": "sql_draft",
        "summary": f"Explained SELECT for {table_name}.",
        "confidence": "medium" if warnings else "high",
        "source_mode": "generated_draft",
        "cost_level": "local",
        "block": {
            "type": "sql_draft",
            "purpose": f"Explain SELECT against {table_name}.",
            "sql": sql_text,
            "parameters": [],
            "tables": [table_name],
            "columns": known_columns,
            "assumptions": ["Only simple single-table SELECT explanation is supported in this foundation slice."],
            "warnings": warnings,
        },
        "sources": [data_dictionary_source(table_name)],
    }
```

- [ ] **Step 4: Run service tests**

Run: `pytest tests/test_assistant_source_index.py -k "sql_helper" -v`

Expected: PASS.

## Task 2: SQL Helper API Endpoints

**Files:**
- Modify: `src/otm_workbench/assistant/routes.py`
- Modify: `tests/test_assistant_source_index.py`

- [ ] **Step 1: Write failing API tests**

```python
def test_assistant_sql_draft_api_requires_auth(client):
    response = client.post(
        "/api/v1/assistant/sql/draft",
        json={
            "table_name": "RATE_GEO_COST",
            "columns": ["RATE_GEO_COST_GROUP_GID"],
            "filter_column": "RATE_GEO_COST_GROUP_GID",
            "purpose": "Find rate geo cost by group.",
        },
    )

    assert response.status_code == 401


def test_assistant_sql_draft_api_returns_select_only_draft(client, admin_header):
    response = client.post(
        "/api/v1/assistant/sql/draft",
        headers=admin_header,
        json={
            "table_name": "RATE_GEO_COST",
            "columns": ["RATE_GEO_COST_GROUP_GID"],
            "filter_column": "RATE_GEO_COST_GROUP_GID",
            "purpose": "Find rate geo cost by group.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer_type"] == "sql_draft"
    assert payload["block"]["tables"] == ["RATE_GEO_COST"]
    assert "delete" not in payload["block"]["sql"].lower()


def test_assistant_sql_explain_api_rejects_mutation(client, admin_header):
    response = client.post(
        "/api/v1/assistant/sql/explain",
        headers=admin_header,
        json={"sql_text": "update shipment set domain_name = 'PUBLIC'"},
    )

    assert response.status_code == 200
    assert response.json()["answer_type"] == "blocked"
```

- [ ] **Step 2: Run API tests to verify RED**

Run: `pytest tests/test_assistant_source_index.py -k "assistant_sql" -v`

Expected: FAIL with `404 Not Found` for `/api/v1/assistant/sql/draft`.

- [ ] **Step 3: Implement API models and endpoints**

Modify `src/otm_workbench/assistant/routes.py`:

```python
from otm_workbench.assistant.sql_helper import draft_single_table_select, explain_select_sql
```

Add models:

```python
class SqlDraftRequest(BaseModel):
    table_name: str
    columns: list[str]
    filter_column: str
    purpose: str = "Draft a safe OTM SELECT."


class SqlExplainRequest(BaseModel):
    sql_text: str
```

Add helper:

```python
def dictionary_root() -> Path:
    return Path(get_settings().otm_data_dictionary_root)
```

Add endpoints:

```python
@router.post("/sql/draft")
def draft_sql(request: SqlDraftRequest, user: User = Depends(require_user)):
    return draft_single_table_select(
        dictionary_root(),
        table_name=request.table_name,
        columns=request.columns,
        filter_column=request.filter_column,
        purpose=request.purpose,
    )


@router.post("/sql/explain")
def explain_sql(request: SqlExplainRequest, user: User = Depends(require_user)):
    return explain_select_sql(dictionary_root(), request.sql_text)
```

- [ ] **Step 4: Run API tests**

Run: `pytest tests/test_assistant_source_index.py -k "assistant_sql" -v`

Expected: PASS.

## Task 3: Validation And Documentation

**Files:**
- Modify: `docs/agent/assistant-planning/SQL_HELPER_DESIGN.md`
- Modify: `docs/agent/HANDOFF.md`
- Modify: `docs/agent/VALIDATION_REPORT.md`

- [ ] **Step 1: Run focused validation**

Run: `pytest tests/test_assistant_source_index.py -v`

Expected: PASS.

- [ ] **Step 2: Run navigation regression**

Run: `pytest tests/test_modules_navigation.py::test_assistant_is_not_added_to_main_navigation -v`

Expected: PASS.

- [ ] **Step 3: Run Catalog smoke**

Run: `pytest tests/test_catalog_core.py -v`

Expected: PASS.

- [ ] **Step 4: Run incompleteness scan**

Run: `rg -n "T[O]DO|T[B]D|place[Hh]older|implement late[r]|fill i[n]" src/otm_workbench/assistant tests/test_assistant_source_index.py docs/agent/assistant-planning docs/superpowers/plans/2026-05-28-workbench-assistant-sql-helper-foundation.md`

Expected: no output.

- [ ] **Step 5: Update documentation**

Add to `docs/agent/assistant-planning/SQL_HELPER_DESIGN.md`:

```markdown
## Implemented Foundation

The first SQL Helper foundation supports deterministic local behavior only:

- unsafe mutation and DDL SQL are blocked;
- single-table SELECT drafts require Data Dictionary table and column matches;
- pasted single-table SELECT SQL can be explained with known and unknown columns;
- no SQL is executed;
- joins, saved query persistence, and AI generation remain outside this slice.
```

Add matching validation notes to `docs/agent/HANDOFF.md` and `docs/agent/VALIDATION_REPORT.md`.

## Self-Review

Spec coverage:
- SQL helper remains lightweight and local-only.
- No LLM or web/API calls are introduced.
- Unsafe mutation and DDL requests are blocked.
- Table and column truth comes from the Data Dictionary.
- Output uses structured response fields aligned with the Assistant response contract.
- Joins and saved query persistence are explicitly deferred.

Risks:
- The simple parser is intentionally limited and should not be mistaken for a full SQL parser.
- This first slice should not execute SQL under any condition.
- Multi-table queries should return clarification or limited explanation until join patterns exist.

Execution recommendation:
Implement with inline TDD unless a real subagent tool is available, because this is a tightly coupled small backend slice.
