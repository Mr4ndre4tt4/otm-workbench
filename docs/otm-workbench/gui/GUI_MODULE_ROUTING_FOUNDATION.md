# GUI Module Routing Foundation

**Status:** implemented
**Branch:** `codex/gui-module-routing-foundation`

## Objective

Establish a reusable module routing layer for the browser-first GUI without
moving navigation ownership to the frontend.

The backend remains responsible for deciding which modules a user can see
through:

```text
GET /api/v1/platform/navigation
```

The frontend uses the returned `path`, `label`, `status`, and `id` to render the
current route.

Route composition is centralized in:

```text
frontend/src/app/routes/WorkbenchRoute.tsx
```

`App.tsx` remains the shell orchestrator and should not own concrete module
dispatch branches.

## Routing Rules

```text
/      -> Project Cockpit
/home  -> Project Cockpit
/<backend navigation path> -> shared module workspace template
unknown route -> module unavailable state
```

The sidebar now uses SPA navigation through React Router while preserving the
backend-owned navigation items.

## Shared Module Template

The first module route template contains:

- Page header
- Module status chip
- Overview panel
- Side panel for expected reusable areas:
  - primary list or work queue
  - selected object summary
  - available actions from backend
  - jobs, artifacts, and evidence links

This is intentionally table/detail oriented. Custom visual experiences should
be added only when the module needs them and after the backend contract is
stable.

## Next Step

Attach the first real module read model to this route foundation. The natural
candidate is Rates Studio because the backend already has summary, batches,
validation, approval, CSV preview, and export contracts.

## Validation

- `frontend/src/app/App.test.tsx` verifies `/rates` renders from backend
  navigation metadata.
- `frontend/tests/routeCompositionContract.test.ts` verifies route dispatch
  stays out of `App.tsx`.
- Navigation remains contract-driven; no real client data or client-specific
  examples are required.
