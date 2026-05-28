# Workbench Assistant SQL Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only SQL Helper draft form to the embedded Workbench Assistant panel.

**Architecture:** Reuse the existing backend `/api/v1/assistant/sql/draft` endpoint. The frontend collects table, columns, filter column, and purpose, then displays the returned draft SQL, warnings, assumptions, and dictionary source hints without executing SQL.

**Tech Stack:** React, Vite, Testing Library, Vitest, existing FastAPI Assistant endpoints.

---

## File Structure

- Modify `frontend/src/platform/types/assistant.ts`
  - Add SQL draft response types.
- Modify `frontend/src/platform/hooks/assistant.ts`
  - Add `draftAssistantSql` API helper.
- Modify `frontend/src/app/shell/WorkbenchAssistant.tsx`
  - Add SQL Helper state, form, submit handler, and read-only result preview.
- Modify `frontend/src/app/shell/shell.css`
  - Add compact SQL preview styling.
- Modify `frontend/src/app/AppFunctionalShell.test.tsx`
  - Extend Assistant functional test to cover SQL draft request/preview.
- Modify `frontend/scripts/functional-assistant-browser.mjs`
  - Exercise the SQL draft panel in browser QA.
- Update docs and handoff.

## Task 1: Functional RED Test

- [x] **Step 1: Extend the Assistant functional test**

Add assertions that the Assistant panel exposes SQL fields named:

```text
SQL table
SQL columns
SQL filter column
SQL purpose
```

Then submit a draft for:

```json
{
  "table_name": "RATE_GEO_COST",
  "columns": ["RATE_GEO_COST_GROUP_GID", "COST"],
  "filter_column": "RATE_GEO_COST_GROUP_GID",
  "purpose": "Find rate cost by group"
}
```

Expect the panel to render:

```text
SQL draft preview
select rgc.RATE_GEO_COST_GROUP_GID, rgc.COST from RATE_GEO_COST rgc where rgc.RATE_GEO_COST_GROUP_GID = :rate_geo_cost_group_gid
Review before use; Assistant drafts are not executed.
```

- [x] **Step 2: Run RED**

```powershell
npm test -- src/app/AppFunctionalShell.test.tsx -t "opens the Workbench Assistant shell"
```

Expected result: test fails because the SQL form is not in the panel yet.

## Task 2: SQL API Helper And Types

- [x] **Step 1: Add SQL draft types**

Add typed structures for `AssistantSqlDraft`, `AssistantSqlDraftBlock`, and
`AssistantSqlDraftRequest`.

- [x] **Step 2: Add API helper**

Add `draftAssistantSql(token, payload)` that posts to
`/api/v1/assistant/sql/draft`.

## Task 3: Assistant SQL Form

- [x] **Step 1: Add form state**

Track table, columns, filter column, purpose, loading state, error, and returned
draft payload.

- [x] **Step 2: Render read-only SQL draft section**

Add a compact form under the Oracle lookup area with a `Draft SQL` button.
Render returned SQL inside a read-only preview block and show warnings.

- [x] **Step 3: Run GREEN**

```powershell
npm test -- src/app/AppFunctionalShell.test.tsx -t "opens the Workbench Assistant shell"
```

Expected result: focused Assistant shell test passes.

## Task 4: Browser QA And Docs

- [x] **Step 1: Update browser QA script**

Exercise the SQL form and assert the SQL preview appears.

- [x] **Step 2: Run validation**

```powershell
npm test -- src/app/AppFunctionalShell.test.tsx
npm run build
pytest tests/test_modules_navigation.py::test_assistant_is_not_added_to_main_navigation -v
npm run qa:functional:assistant:browser
```

- [x] **Step 3: Run incompleteness and whitespace scans**

```powershell
rg -n "T[O]DO|T[B]D|implement late[r]|fill i[n]" frontend/src/app/shell frontend/src/app/AppFunctionalShell.test.tsx docs/agent/assistant-planning docs/superpowers/plans/2026-05-28-workbench-assistant-sql-panel.md docs/agent/HANDOFF.md docs/agent/VALIDATION_REPORT.md
git diff --check -- frontend/src/app/shell/WorkbenchAssistant.tsx frontend/src/app/shell/shell.css frontend/src/app/AppFunctionalShell.test.tsx frontend/src/platform/hooks/assistant.ts frontend/src/platform/types/assistant.ts frontend/scripts/functional-assistant-browser.mjs docs/agent/assistant-planning/UI_EXPERIENCE_SPEC.md docs/superpowers/plans/2026-05-28-workbench-assistant-sql-panel.md docs/agent/HANDOFF.md docs/agent/VALIDATION_REPORT.md
```

- [x] **Step 4: Final report**

Report changed files, validation evidence, browser screenshot path, and the
dirty-worktree caveat.

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
Focused Assistant SQL panel test: RED before implementation, then passed.
AppFunctionalShell.test.tsx: 2 passed.
Frontend build: passed with existing Vite large chunk warning.
Assistant navigation regression: 1 passed.
Assistant backend tests: 44 passed after rerun with a longer timeout.
Assistant browser QA: passed; screenshot refreshed at var/qa/workbench-assistant-shell.png.
```
