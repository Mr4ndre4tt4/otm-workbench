# Workbench Assistant Joined SQL Draft Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate a deterministic two-table SELECT draft from an approved Assistant join pattern.

**Architecture:** Keep SQL generation local and source-bound. The SQL Helper validates requested output/filter columns against the Data Dictionary, requires an approved `AssistantJoinPattern`, then assembles a parameterized SELECT with citations and warnings.

**Tech Stack:** FastAPI, SQLAlchemy, SQLite test database, local OTM Data Dictionary, pytest.

---

## File Structure

- Modify `src/otm_workbench/assistant/sql_helper.py`
  - Add `draft_joined_select`.
  - Reuse existing identifier normalization, aliasing, table/column validation,
    blocked response, and source metadata helpers.
- Modify `src/otm_workbench/assistant/routes.py`
  - Add `SqlJoinedDraftRequest`.
  - Add `POST /api/v1/assistant/sql/draft-join`.
- Modify `tests/test_assistant_source_index.py`
  - Add service and API tests for approved-pattern join SQL generation.
  - Add blocking tests for draft patterns and invalid requested columns.
- Update Assistant planning docs and handoff after validation.

## Task 1: Joined SQL Helper Service

**Files:**

- Modify: `tests/test_assistant_source_index.py`
- Modify: `src/otm_workbench/assistant/sql_helper.py`

- [ ] **Step 1: Write failing service tests**

Add tests that:

- create an approved `SHIPMENT` to `SHIPMENT_STOP` join pattern;
- call `draft_joined_select`;
- assert the SQL includes a deterministic join using the approved pattern;
- assert the response includes both tables, requested columns, the join pattern
  ID, a bind parameter, and high confidence;
- assert a draft pattern blocks SQL generation;
- assert an unknown requested output column blocks SQL generation.

- [ ] **Step 2: Run focused RED test**

Run:

```powershell
pytest tests/test_assistant_source_index.py -k "joined_sql" -v
```

Expected:

```text
FAIL: ImportError or AttributeError for draft_joined_select
```

- [ ] **Step 3: Implement minimal service**

Add `draft_joined_select(db, dictionary_root, join_pattern_id, left_columns,
right_columns, filter_table, filter_column, purpose)` to `sql_helper.py`.

Rules:

- load `AssistantJoinPattern` by ID;
- block when missing or not `APPROVED`;
- validate output and filter columns against the Data Dictionary;
- use aliases from `alias_for_table`;
- support `INNER` and `LEFT` joins directly;
- support `EXISTS` by returning a blocked response for now, because EXISTS
  draft shape requires a separate product decision;
- return `answer_type: sql_draft`, `source_mode: generated_draft`,
  `cost_level: local`, and `confidence: high` when no warnings exist.

- [ ] **Step 4: Run focused GREEN test**

Run:

```powershell
pytest tests/test_assistant_source_index.py -k "joined_sql" -v
```

Expected:

```text
All selected joined SQL service tests pass.
```

## Task 2: Joined SQL API Endpoint

**Files:**

- Modify: `tests/test_assistant_source_index.py`
- Modify: `src/otm_workbench/assistant/routes.py`

- [ ] **Step 1: Write failing API test**

Add a test that:

- creates and approves a join pattern through the existing API;
- calls `POST /api/v1/assistant/sql/draft-join`;
- asserts the endpoint returns a two-table SQL draft and does not execute SQL.

- [ ] **Step 2: Run focused RED test**

Run:

```powershell
pytest tests/test_assistant_source_index.py -k "joined_sql_api" -v
```

Expected:

```text
FAIL: 404 for /api/v1/assistant/sql/draft-join
```

- [ ] **Step 3: Implement route**

Add a request model:

```python
class SqlJoinedDraftRequest(BaseModel):
    join_pattern_id: str
    left_columns: list[str]
    right_columns: list[str]
    filter_table: str
    filter_column: str
    purpose: str = "Draft a safe joined OTM SELECT."
```

Add route:

```python
@router.post("/sql/draft-join")
def draft_joined_sql(request: SqlJoinedDraftRequest, db: Session = Depends(get_db), user: User = Depends(require_user)):
    return draft_joined_select(...)
```

- [ ] **Step 4: Run focused GREEN test**

Run:

```powershell
pytest tests/test_assistant_source_index.py -k "joined_sql" -v
```

Expected:

```text
All selected joined SQL service and API tests pass.
```

## Task 3: Validation And Documentation

**Files:**

- Modify: `docs/agent/assistant-planning/SQL_HELPER_DESIGN.md`
- Modify: `docs/agent/assistant-planning/QUERY_CORPUS_STRATEGY.md`
- Modify: `docs/agent/HANDOFF.md`
- Modify: `docs/agent/VALIDATION_REPORT.md`

- [ ] **Step 1: Run backend validation**

Run:

```powershell
pytest tests/test_assistant_source_index.py -v
pytest tests/test_modules_navigation.py::test_assistant_is_not_added_to_main_navigation -v
pytest tests/test_catalog_core.py -v
```

Expected:

```text
Assistant tests pass.
Navigation regression passes.
Catalog core tests pass.
```

- [ ] **Step 2: Run incompleteness scan**

Run:

```powershell
rg -n "T[O]DO|T[B]D|place[Hh]older|implement late[r]|fill i[n]" src/otm_workbench/assistant tests/test_assistant_source_index.py docs/agent/assistant-planning docs/superpowers/plans/2026-05-28-workbench-assistant-joined-sql-draft.md docs/agent/HANDOFF.md docs/agent/VALIDATION_REPORT.md
```

Expected:

```text
No matches.
```

- [ ] **Step 3: Update docs**

Document that joined SQL draft generation now exists only when the caller
chooses an approved join pattern. Keep automatic relationship discovery,
multi-hop joins, EXISTS SQL generation, and UI integration out of scope.

- [ ] **Step 4: Final report**

Report changed files, validation results, skipped frontend/browser validation,
and dirty-worktree caveat.
