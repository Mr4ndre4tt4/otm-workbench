# Workbench Assistant Oracle Docs Cache Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a safe backend foundation for Oracle documentation lookup using approved official URLs and a local searchable cache.

**Architecture:** The Assistant stores Oracle documentation references as reviewed cache records. Searches return only official Oracle documentation URLs from the local cache; live web/API lookup remains an explicit future action so the Workbench does not create hidden network cost or stale-source confusion.

**Tech Stack:** FastAPI, SQLAlchemy, SQLite test database, pytest, local Assistant backend package.

---

## File Structure

- Modify `src/otm_workbench/models.py`
  - Add `AssistantOracleDocCache` with URL, title, product area, topic,
    summary, version label, status, reviewed metadata, and fetched timestamp.
- Create `src/otm_workbench/assistant/oracle_docs.py`
  - Validate official Oracle documentation URLs.
  - Create cache records.
  - Approve records.
  - Search approved records by query text, product area, and topic.
  - Return blocked response for live web lookup requests.
- Modify `src/otm_workbench/assistant/routes.py`
  - Add create, approve, search, and live lookup request endpoints under
    `/api/v1/assistant/oracle-docs`.
- Modify `tests/test_assistant_source_index.py`
  - Add service and API tests.
- Update Assistant planning docs and handoff after validation.

## Task 1: Oracle Docs Cache Service

**Files:**

- Modify: `tests/test_assistant_source_index.py`
- Modify: `src/otm_workbench/models.py`
- Create: `src/otm_workbench/assistant/oracle_docs.py`

- [ ] **Step 1: Write failing service tests**

Add tests that:

- create a draft Oracle docs cache record for an official `docs.oracle.com`
  URL;
- reject a non-Oracle URL;
- approve a draft record;
- search returns only approved records by default;
- live web lookup returns a blocked local response.

- [ ] **Step 2: Run focused RED test**

Run:

```powershell
pytest tests/test_assistant_source_index.py -k "oracle_docs" -v
```

Expected:

```text
FAIL: missing oracle_docs module or missing AssistantOracleDocCache model.
```

- [ ] **Step 3: Implement minimal model and service**

Add `AssistantOracleDocCache` and a focused service with:

- `is_official_oracle_doc_url(url)`;
- `create_oracle_doc_cache(...)`;
- `approve_oracle_doc_cache(...)`;
- `search_oracle_doc_cache(...)`;
- `blocked_live_lookup(query_text)`;
- `serialize_oracle_doc_cache(record)`.

URL rules:

- allow `https://docs.oracle.com/...`;
- allow `https://www.oracle.com/.../documentation/...`;
- reject all other domains and schemes.

- [ ] **Step 4: Run focused GREEN test**

Run:

```powershell
pytest tests/test_assistant_source_index.py -k "oracle_docs" -v
```

Expected:

```text
All selected Oracle docs cache service tests pass.
```

## Task 2: Oracle Docs Cache API

**Files:**

- Modify: `tests/test_assistant_source_index.py`
- Modify: `src/otm_workbench/assistant/routes.py`

- [ ] **Step 1: Write failing API tests**

Add tests that:

- create an Oracle docs cache record as admin;
- approve it as admin;
- search it as an authenticated user;
- request live lookup and receive a blocked response instead of network access.

- [ ] **Step 2: Run focused RED test**

Run:

```powershell
pytest tests/test_assistant_source_index.py -k "oracle_docs_api" -v
```

Expected:

```text
FAIL: 404 for Oracle docs endpoints.
```

- [ ] **Step 3: Implement routes**

Add request models and endpoints:

- `POST /api/v1/assistant/oracle-docs/cache`
- `POST /api/v1/assistant/oracle-docs/cache/{record_id}/approve`
- `GET /api/v1/assistant/oracle-docs/search`
- `POST /api/v1/assistant/oracle-docs/live-lookup`

Admin role is required for cache creation and approval. User auth is enough for
search and blocked live lookup requests.

- [ ] **Step 4: Run focused GREEN test**

Run:

```powershell
pytest tests/test_assistant_source_index.py -k "oracle_docs" -v
```

Expected:

```text
All selected Oracle docs service and API tests pass.
```

## Task 3: Validation And Documentation

**Files:**

- Modify: `docs/agent/assistant-planning/README.md`
- Modify: `docs/agent/assistant-planning/ORACLE_DOCS_CONNECTOR_POLICY.md`
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
rg -n "T[O]DO|T[B]D|place[Hh]older|implement late[r]|fill i[n]" src/otm_workbench/assistant tests/test_assistant_source_index.py docs/agent/assistant-planning docs/superpowers/plans/2026-05-28-workbench-assistant-oracle-docs-cache.md docs/agent/HANDOFF.md docs/agent/VALIDATION_REPORT.md
```

Expected:

```text
No matches.
```

- [ ] **Step 3: Update docs**

Document that this slice enables local cached Oracle documentation search only.
Live web/API lookup, crawling, summarization, freshness checks, and page-opening
UI remain separate future slices.

- [ ] **Step 4: Final report**

Report changed files, validation results, skipped frontend/browser validation,
and dirty-worktree caveat.
