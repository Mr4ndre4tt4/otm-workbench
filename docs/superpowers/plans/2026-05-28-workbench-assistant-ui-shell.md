# Workbench Assistant UI Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first embedded Workbench Assistant UI shell without adding a top-level module.

**Architecture:** Render an authenticated fixed overlay inside `WorkbenchShell`: a small lower-right robot-trucker launcher opens a compact panel. The panel calls existing Assistant backend endpoints for health, local search, and Oracle lookup request preparation; it does not execute live web lookup or introduce navigation items.

**Tech Stack:** React, Vite, TanStack Query, FastAPI endpoints, Vitest, Testing Library.

---

## File Structure

- Create `frontend/src/platform/types/assistant.ts`
  - Types for Assistant health, source search results, and Oracle lookup request responses.
- Create `frontend/src/platform/hooks/assistant.ts`
  - `useAssistantHealth(token)`
  - `useAssistantSearch(token, query, enabled)`
  - `prepareOracleLookup(token, query, privateTerms)`
- Modify `frontend/src/platform/types.ts`
  - Export Assistant types.
- Modify `frontend/src/platform/hooks.ts`
  - Export Assistant hooks.
- Create `frontend/src/app/shell/WorkbenchAssistant.tsx`
  - Launcher, panel, local source search, Oracle lookup preview.
- Modify `frontend/src/app/shell/WorkbenchShell.tsx`
  - Render Assistant only when authenticated and token exists.
- Modify `frontend/src/app/shell/index.ts`
  - Export Assistant component if useful.
- Modify `frontend/src/app/shell/shell.css`
  - Fixed overlay and compact panel styling.
- Modify `frontend/src/app/AppFunctionalShell.test.tsx`
  - Add functional assertions for launcher, panel, search, and Oracle preview.

## Task 1: Functional RED Test

**Files:**

- Modify: `frontend/src/app/AppFunctionalShell.test.tsx`

- [ ] **Step 1: Write failing test**

Add a test that logs in, verifies no `Assistant` navigation item exists, opens
the lower-right Assistant launcher, verifies health and search wiring, submits
a local search, and prepares an Oracle lookup request.

- [ ] **Step 2: Run RED**

Run:

```powershell
npm test -- src/app/AppFunctionalShell.test.tsx -t "opens the Workbench Assistant shell"
```

Expected:

```text
FAIL: launcher button is not found.
```

## Task 2: Assistant Frontend API Layer

**Files:**

- Create: `frontend/src/platform/types/assistant.ts`
- Create: `frontend/src/platform/hooks/assistant.ts`
- Modify: `frontend/src/platform/types.ts`
- Modify: `frontend/src/platform/hooks.ts`

- [ ] **Step 1: Implement types and hooks**

Add typed wrappers around:

- `GET /api/v1/assistant/health`
- `GET /api/v1/assistant/search?query=...`
- `POST /api/v1/assistant/oracle-docs/live-lookup`

- [ ] **Step 2: Run focused test**

Run the same focused shell test and expect a component failure until the UI is
created.

## Task 3: Assistant Shell Component

**Files:**

- Create: `frontend/src/app/shell/WorkbenchAssistant.tsx`
- Modify: `frontend/src/app/shell/WorkbenchShell.tsx`
- Modify: `frontend/src/app/shell/index.ts`
- Modify: `frontend/src/app/shell/shell.css`

- [ ] **Step 1: Implement component**

The component must:

- use a small fixed lower-right icon button with accessible name
  `Open Workbench Assistant`;
- display panel title `Workbench Assistant`;
- show backend health status;
- accept a local source search query;
- render search result titles and source links;
- prepare Oracle lookup and render sanitized query plus official Oracle action;
- close using an icon button named `Close Workbench Assistant`;
- stay outside sidebar navigation.

- [ ] **Step 2: Run focused GREEN**

Run:

```powershell
npm test -- src/app/AppFunctionalShell.test.tsx -t "opens the Workbench Assistant shell"
```

Expected:

```text
Focused shell Assistant test passes.
```

## Task 4: Validation And Documentation

**Files:**

- Modify: `docs/agent/HANDOFF.md`
- Modify: `docs/agent/VALIDATION_REPORT.md`
- Modify: `docs/agent/assistant-planning/UI_EXPERIENCE_SPEC.md`

- [ ] **Step 1: Run frontend validation**

Run:

```powershell
npm test -- src/app/AppFunctionalShell.test.tsx
npm run build
```

- [ ] **Step 2: Run backend smoke validation**

Run:

```powershell
pytest tests/test_assistant_source_index.py -v
pytest tests/test_modules_navigation.py::test_assistant_is_not_added_to_main_navigation -v
```

- [ ] **Step 3: Run browser QA**

Start backend/frontend as needed, verify live navigation first, open the shell,
open the Assistant, and capture a screenshot.

- [ ] **Step 4: Run incompleteness scan**

Run:

```powershell
rg -n "T[O]DO|T[B]D|place[Hh]older|implement late[r]|fill i[n]" frontend/src/app/shell frontend/src/platform/hooks/assistant.ts frontend/src/platform/types/assistant.ts tests/test_assistant_source_index.py docs/agent/assistant-planning docs/superpowers/plans/2026-05-28-workbench-assistant-ui-shell.md docs/agent/HANDOFF.md docs/agent/VALIDATION_REPORT.md
```

- [ ] **Step 5: Final report**

Report changed files, validation results, browser QA evidence, and dirty-worktree caveat.
