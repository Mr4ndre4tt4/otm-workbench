# Workbench Assistant Oracle Lookup Request Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert an Oracle documentation question into a sanitized explicit lookup request with official Oracle search links and no automatic network access.

**Architecture:** Extend the Oracle docs Assistant service with deterministic query sanitization and official search-link generation. The endpoint returns a `lookup_request` payload that the UI can display as an explicit user action before any future live web connector runs.

**Tech Stack:** FastAPI, Pydantic, local Assistant backend package, pytest.

---

## File Structure

- Modify `src/otm_workbench/assistant/oracle_docs.py`
  - Add query sanitization helpers.
  - Add official Oracle search URL generation.
  - Add `prepare_live_lookup_request`.
- Modify `src/otm_workbench/assistant/routes.py`
  - Change `/api/v1/assistant/oracle-docs/live-lookup` from a pure blocked
    response to a prepared explicit lookup request.
- Modify `tests/test_assistant_source_index.py`
  - Add service and API tests for sanitization, official URLs, and no network
    execution.
- Update Assistant planning docs and handoff after validation.

## Task 1: Sanitized Lookup Request Service

**Files:**

- Modify: `tests/test_assistant_source_index.py`
- Modify: `src/otm_workbench/assistant/oracle_docs.py`

- [ ] **Step 1: Write failing service tests**

Add tests that:

- sanitize client/project/environment/private URL/token-looking terms from a
  user query;
- keep useful OTM/Oracle terms such as `REST API`, `shipment`, and `endpoint`;
- generate only official Oracle search URLs;
- return `answer_type: lookup_request`, `cost_level: web`, and
  `network_performed: False`.

- [ ] **Step 2: Run focused RED test**

Run:

```powershell
pytest tests/test_assistant_source_index.py -k "oracle_lookup_request" -v
```

Expected:

```text
FAIL: missing prepare_live_lookup_request or old blocked live lookup payload.
```

- [ ] **Step 3: Implement minimal service**

Add:

- `sanitize_oracle_doc_query(query_text, private_terms=None)`;
- `oracle_search_links(sanitized_query)`;
- `prepare_live_lookup_request(query_text, private_terms=None)`.

Rules:

- remove explicit private terms supplied by the caller;
- remove URL-like tokens;
- remove token-like long alphanumeric strings;
- collapse whitespace;
- generate links only under `https://docs.oracle.com/search/`;
- do not perform network calls.

- [ ] **Step 4: Run focused GREEN test**

Run:

```powershell
pytest tests/test_assistant_source_index.py -k "oracle_lookup_request" -v
```

Expected:

```text
All selected Oracle lookup request service tests pass.
```

## Task 2: Lookup Request API

**Files:**

- Modify: `tests/test_assistant_source_index.py`
- Modify: `src/otm_workbench/assistant/routes.py`

- [ ] **Step 1: Write failing API test**

Add a test that posts to:

```text
POST /api/v1/assistant/oracle-docs/live-lookup
```

with `query` and `private_terms`, then asserts:

- status `200`;
- `answer_type` is `lookup_request`;
- `network_performed` is `False`;
- generated URLs start with `https://docs.oracle.com/search/`;
- private terms are absent from the sanitized query and URLs.

- [ ] **Step 2: Run focused RED test**

Run:

```powershell
pytest tests/test_assistant_source_index.py -k "oracle_lookup_request_api" -v
```

Expected:

```text
FAIL: live lookup endpoint still returns blocked payload or ignores private_terms.
```

- [ ] **Step 3: Implement route update**

Update `OracleDocLiveLookupRequest` to include:

```python
private_terms: list[str] = []
```

Update the route to return `prepare_live_lookup_request(...)`.

- [ ] **Step 4: Run focused GREEN test**

Run:

```powershell
pytest tests/test_assistant_source_index.py -k "oracle_lookup_request" -v
```

Expected:

```text
All selected Oracle lookup request service and API tests pass.
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
rg -n "T[O]DO|T[B]D|place[Hh]older|implement late[r]|fill i[n]" src/otm_workbench/assistant tests/test_assistant_source_index.py docs/agent/assistant-planning docs/superpowers/plans/2026-05-28-workbench-assistant-oracle-lookup-request.md docs/agent/HANDOFF.md docs/agent/VALIDATION_REPORT.md
```

Expected:

```text
No matches.
```

- [ ] **Step 3: Update docs**

Document that the assistant can prepare an explicit official Oracle lookup
request but still does not execute a web search or scrape pages.

- [ ] **Step 4: Final report**

Report changed files, validation results, skipped frontend/browser validation,
and dirty-worktree caveat.
