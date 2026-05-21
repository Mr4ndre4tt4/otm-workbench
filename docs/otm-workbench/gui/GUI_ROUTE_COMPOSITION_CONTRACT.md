# GUI Route Composition Contract

**Status:** delivered  
**Branch:** `codex/gui-route-composition-contract`  
**Scope:** app shell orchestration versus route/module composition.

## 1. Purpose

`App.tsx` should remain the top-level data and auth orchestrator. It wires the
auth gate, backend navigation query, backend preference query, current path, and
route content.

The reusable visual app frame lives in:

```text
frontend/src/app/shell/WorkbenchShell.tsx
```

Route selection, Project Cockpit rendering, concrete module view dispatch, and
fallback route states belong in:

```text
frontend/src/app/routes/WorkbenchRoute.tsx
```

This keeps the app root stable as new modules are added.

## 2. Ownership Boundary

`App.tsx` may own:

```text
- AuthProvider-derived shell gate usage
- backend navigation query wiring
- backend user preference query wiring
- current route path
- authenticated route versus login selection
```

`WorkbenchRoute.tsx` may own:

```text
- Project Cockpit route composition
- backend navigation item path matching
- explicit active module view dispatch
- placeholder-only module fallback
- unknown route fallback
```

Neither file owns backend business decisions. Navigation availability,
permissions, readiness, lifecycle, actions, jobs, artifacts, evidence, active
context, and preferences remain backend-owned.

## 3. Required Behavior

```text
1. / and /home render Project Cockpit.
2. Backend navigation paths render the matching module view when explicitly wired.
3. Placeholder-only modules use the shared module placeholder.
4. Unknown routes render the backend navigation unavailable state.
5. New module route branches are added only in WorkbenchRoute.tsx.
```

## 4. Guardrails

```text
frontend/tests/routeCompositionContract.test.ts
frontend/tests/moduleNavigationContract.test.ts
```

The tests prevent route dispatch from drifting back into `App.tsx` and keep the
module navigation contract aligned with the centralized `WorkbenchRoute`
composition file.
