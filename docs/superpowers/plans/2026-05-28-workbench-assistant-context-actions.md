# Workbench Assistant Context Actions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the embedded Assistant aware of the current Workbench route and expose first-pass quick actions without adding a navigation module.

**Architecture:** Pass the current path and backend-owned navigation items from `WorkbenchShell` into `WorkbenchAssistant`. The Assistant derives a current module label from the active route and renders a compact context strip plus deterministic quick-action buttons that prefill existing local search and Oracle lookup fields.

**Tech Stack:** React, Vite, Testing Library, Vitest.

---

## File Structure

- Modify `frontend/src/app/shell/WorkbenchShell.tsx`
  - Pass `currentPath` and `navigationItems` to `WorkbenchAssistant`.
- Modify `frontend/src/app/shell/WorkbenchAssistant.tsx`
  - Accept route context props.
  - Derive active module label.
  - Render context strip.
  - Add quick actions.
- Modify `frontend/src/app/shell/shell.css`
  - Add compact context strip and quick-action styles.
- Modify `frontend/src/app/AppFunctionalShell.test.tsx`
  - Add assertions for route context and quick actions.
- Update Assistant planning docs and handoff after validation.

## Task 1: Functional RED Test

**Files:**

- Modify: `frontend/src/app/AppFunctionalShell.test.tsx`

- [x] **Step 1: Write failing test assertions**

Extend the existing Assistant shell functional test to assert:

- the panel shows `Current screen` and `Project Cockpit`;
- quick actions include `Help for this screen`, `Find template`, and
  `Search Oracle docs`;
- clicking `Find template` prefills local source search with a route-aware
  query;
- clicking `Search Oracle docs` prefills the Oracle docs question.

- [x] **Step 2: Run RED**

Run:

```powershell
npm test -- src/app/AppFunctionalShell.test.tsx -t "opens the Workbench Assistant shell"
```

Expected:

```text
FAIL: current screen or quick-action text is not found.
```

## Task 2: Context Strip And Quick Actions

**Files:**

- Modify: `frontend/src/app/shell/WorkbenchShell.tsx`
- Modify: `frontend/src/app/shell/WorkbenchAssistant.tsx`
- Modify: `frontend/src/app/shell/shell.css`

- [x] **Step 1: Implement context props**

Pass `currentPath` and `navigationItems` into the Assistant.

- [x] **Step 2: Implement route matching**

Choose the active module by matching the longest navigation item path that is a
prefix of `currentPath`. Fall back to `Current route` when no match exists.

- [x] **Step 3: Implement quick actions**

Add buttons:

- `Help for this screen` sets local search to `<module label> help`;
- `Find template` sets local search to `<module label> template`;
- `Search Oracle docs` sets Oracle question to `Oracle Transportation Management <module label> documentation`.

- [x] **Step 4: Run GREEN**

Run:

```powershell
npm test -- src/app/AppFunctionalShell.test.tsx -t "opens the Workbench Assistant shell"
```

Expected:

```text
Focused Assistant shell test passes.
```

## Task 3: Validation And Documentation

**Files:**

- Modify: `docs/agent/assistant-planning/UI_EXPERIENCE_SPEC.md`
- Modify: `docs/agent/HANDOFF.md`
- Modify: `docs/agent/VALIDATION_REPORT.md`

- [x] **Step 1: Run validation**

Run:

```powershell
npm test -- src/app/AppFunctionalShell.test.tsx
npm run build
```

- [x] **Step 2: Run incompleteness scan**

Run:

```powershell
rg -n "T[O]DO|T[B]D|implement late[r]|fill i[n]" frontend/src/app/shell frontend/src/app/AppFunctionalShell.test.tsx docs/agent/assistant-planning docs/superpowers/plans/2026-05-28-workbench-assistant-context-actions.md docs/agent/HANDOFF.md docs/agent/VALIDATION_REPORT.md
```

- [x] **Step 3: Final report**

Report changed files, validation results, skipped browser QA if not rerun, and
dirty-worktree caveat.

Completed validation:

```powershell
npm test -- src/app/AppFunctionalShell.test.tsx -t "opens the Workbench Assistant shell"
npm test -- src/app/AppFunctionalShell.test.tsx
npm run build
pytest tests/test_modules_navigation.py::test_assistant_is_not_added_to_main_navigation -v
npm run qa:functional:assistant:browser
```

Results:

```text
Focused Assistant context test: passed after RED/GREEN fixes.
AppFunctionalShell.test.tsx: 2 passed.
Frontend build: passed with existing Vite large chunk warning.
Assistant navigation regression: 1 passed.
Assistant browser QA: passed; screenshot refreshed at var/qa/workbench-assistant-shell.png.
```
