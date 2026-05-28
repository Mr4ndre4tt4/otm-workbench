# Workbench Assistant SQL Explain Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only SQL explanation/review mode to the embedded Workbench Assistant panel.

**Architecture:** Reuse the existing backend `/api/v1/assistant/sql/explain` endpoint. The frontend accepts pasted SELECT text, posts it for Data Dictionary-grounded analysis, and renders the SQL plus warnings/sources without executing the query.

**Tech Stack:** React, Vite, Testing Library, Vitest, existing FastAPI Assistant SQL helper.

---

## File Structure

- Modify `frontend/src/platform/types/assistant.ts`
  - Reuse SQL draft response shape and add a request type for SQL explain.
- Modify `frontend/src/platform/hooks/assistant.ts`
  - Add `explainAssistantSql` API helper.
- Modify `frontend/src/app/shell/WorkbenchAssistant.tsx`
  - Add pasted SQL state, submit handler, and read-only review preview.
- Modify `frontend/src/app/AppFunctionalShell.test.tsx`
  - Extend the Assistant test to cover SQL explain/review.
- Modify `frontend/scripts/functional-assistant-browser.mjs`
  - Exercise the SQL explain panel in browser QA.
- Update docs and handoff.

## Task 1: Functional RED Test

- [x] **Step 1: Extend the Assistant functional test**

Add a mocked `/api/v1/assistant/sql/explain` response and interact with fields:

```text
SQL to review
Review SQL
```

Use this pasted SQL:

```sql
select rgc.RATE_GEO_COST_GROUP_GID, rgc.UNKNOWN_COL from RATE_GEO_COST rgc
```

Expect:

```text
SQL review preview
RATE_GEO_COST.UNKNOWN_COL was not found.
Review before use; Assistant SQL review is not execution.
```

- [x] **Step 2: Run RED**

```powershell
npm test -- src/app/AppFunctionalShell.test.tsx -t "opens the Workbench Assistant shell"
```

Expected result: test fails because the SQL review form is not present.

## Task 2: API Helper And UI

- [x] **Step 1: Add request type and helper**

Add `AssistantSqlExplainRequest` and `explainAssistantSql(token, sqlText)`.

- [x] **Step 2: Add review form**

Add a textarea labeled `SQL to review` and a `Review SQL` button below the
existing draft form.

- [x] **Step 3: Render review preview**

Render returned SQL in a read-only block with warning text and a no-execution
reminder.

- [x] **Step 4: Run GREEN**

```powershell
npm test -- src/app/AppFunctionalShell.test.tsx -t "opens the Workbench Assistant shell"
```

Expected result: focused Assistant shell test passes.

## Task 3: Browser QA And Docs

- [x] **Step 1: Update browser QA script**

Exercise the SQL review form and assert warning text appears.

- [x] **Step 2: Run validation**

```powershell
npm test -- src/app/AppFunctionalShell.test.tsx
npm run build
pytest tests/test_modules_navigation.py::test_assistant_is_not_added_to_main_navigation -v
pytest tests/test_assistant_source_index.py -v
npm run qa:functional:assistant:browser
```

- [x] **Step 3: Run scans**

```powershell
rg -n "T[O]DO|T[B]D|implement late[r]|fill i[n]" frontend/src/app/shell frontend/src/app/AppFunctionalShell.test.tsx docs/agent/assistant-planning docs/superpowers/plans/2026-05-28-workbench-assistant-sql-explain-panel.md docs/agent/HANDOFF.md docs/agent/VALIDATION_REPORT.md
git diff --check -- frontend/src/app/shell/WorkbenchAssistant.tsx frontend/src/app/AppFunctionalShell.test.tsx frontend/src/platform/hooks/assistant.ts frontend/src/platform/types/assistant.ts frontend/scripts/functional-assistant-browser.mjs docs/agent/assistant-planning/UI_EXPERIENCE_SPEC.md docs/superpowers/plans/2026-05-28-workbench-assistant-sql-explain-panel.md docs/agent/HANDOFF.md docs/agent/VALIDATION_REPORT.md
```

- [x] **Step 4: Final report**

Report changed files, validation evidence, screenshot path, and dirty-worktree
caveat.

Completed validation:

```powershell
npm test -- src/app/AppFunctionalShell.test.tsx -t "opens the Workbench Assistant shell"
npm test -- src/app/AppFunctionalShell.test.tsx
npm run build
pytest tests/test_modules_navigation.py::test_assistant_is_not_added_to_main_navigation -v
pytest tests/test_assistant_source_index.py -v
npm run qa:functional:assistant:browser
```

Results:

```text
Focused Assistant SQL review test: RED before implementation, then passed.
AppFunctionalShell.test.tsx: 2 passed.
Frontend build: passed with existing Vite large chunk warning.
Assistant navigation regression: 1 passed.
Assistant backend tests: 44 passed.
Assistant browser QA: passed; screenshot refreshed at var/qa/workbench-assistant-shell.png.
```
