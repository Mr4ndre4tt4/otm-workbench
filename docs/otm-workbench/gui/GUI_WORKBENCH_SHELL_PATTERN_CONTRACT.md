# GUI Workbench Shell Pattern Contract

**Status:** delivered  
**Branch:** `codex/gui-workbench-shell-contract`  
**Scope:** reusable app frame for brand, sidebar, topbar, preferences, and route content.

## 1. Purpose

`WorkbenchShell` is the shared browser-first frame for OTM Workbench.

It keeps the visual shell out of `App.tsx` and out of individual modules so new
screens reuse the same brand lockup, sidebar placement, topbar actions,
preference controls, and content slot.

## 2. Ownership Boundary

`App.tsx` owns:

```text
- auth state wiring
- backend navigation query wiring
- backend user preference query wiring
- current route path
- authenticated route versus login selection
```

`WorkbenchShell` owns:

```text
- app-shell layout attributes
- brand lockup
- sidebar placement
- sidebar collapse/expand control placement
- topbar placement
- sign out action placement
- preference control placement
- shared route content slot
```

Modules must not create their own app frame, sidebar, topbar, preference
toolbar, or brand lockup.

## 3. Backend Ownership

`WorkbenchShell` renders values received from backend-owned contracts. It does
not decide:

```text
- which modules are visible
- which actions are authorized
- which theme, density, or sidebar mode is durable
- whether a project context is ready
- whether a user can sign in or out
```

Those decisions remain in backend contracts or the platform auth/session layer.

## 4. Required Behavior

```text
1. Render data-theme, data-density, and data-sidebar from user preferences.
2. Render sidebar navigation from backend navigation items.
3. Render sign out only for authenticated sessions.
4. Disable preference controls when no backend session token exists.
5. Render sidebar collapse/expand from the sidebar, not as a topbar preference.
6. Render route content through a child slot without inspecting module internals.
```

## 5. Guardrails

```text
frontend/src/app/shell/WorkbenchShell.test.tsx
frontend/tests/workbenchShellPatternContract.test.ts
frontend/tests/reactBoundary.test.ts
```

The tests verify shell rendering, backend-owned preference attributes, sign-out
visibility, disabled unauthenticated preferences, shell barrel export, and that
`App.tsx` does not own shell frame markup.
