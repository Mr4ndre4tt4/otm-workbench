# GUI Module Workspace Layout Pattern Contract

**Status:** delivered  
**Branch:** `codex/gui-module-workspace-layout-contract`  
**Scope:** shared module workspace grid and primary/side panel placement.

## 1. Purpose

`ModuleWorkspaceLayout` is the shared two-column workspace pattern for module
views.

It keeps `module-template` and `module-template-main` markup centralized in the
UI kit so each module can focus on backend-owned data, selected object state,
actions, jobs, artifacts, and evidence instead of rebuilding the page frame.

## 2. Ownership Boundary

`ModuleWorkspaceLayout` owns:

```text
- module workspace section markup
- primary panel heading
- primary panel backend status chip
- primary content slot
- side content slot
```

`ModuleWorkspaceSide` owns:

```text
- generic module-template-side markup for placeholder or supporting panels
```

`SelectedObjectPanel` remains the preferred side panel for selected object
details.

Module views own:

```text
- backend hook calls
- selected object id state
- mapping backend rows into shared UI kit props
- module-specific actions and evidence/artifact content
```

## 3. Backend Ownership

The layout does not decide readiness, permissions, lifecycle, action
availability, validation status, or module visibility. It renders status and
content supplied by backend-owned contracts.

## 4. Required Behavior

```text
1. Every module view with the standard object/detail workspace uses ModuleWorkspaceLayout.
2. Raw module-template and module-template-main classes stay inside
   `ui/components/layouts.tsx`.
3. Placeholder route side content uses ModuleWorkspaceSide.
4. Selected object details continue to use SelectedObjectPanel.
5. Custom module layouts require an exception in GUI_EXCEPTIONS_REGISTER.md.
```

## 5. Guardrails

```text
frontend/src/ui/components.test.tsx
frontend/tests/moduleWorkspaceLayoutPatternContract.test.ts
frontend/tests/selectedObjectPatternContract.test.ts
```

The tests verify component rendering and prevent module views from owning raw
workspace grid markup.
