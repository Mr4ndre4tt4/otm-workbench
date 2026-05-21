# GUI Load Plan View

**Status:** implemented
**Branch:** `codex/gui-load-plan-view`

## Objective

Add the first backend-backed Load Plan screen using the shared GUI foundation.

Load Plan now renders package summary, package list, and selected package load
sequence from backend contracts instead of the generic module placeholder.

## Backend Contracts

The GUI consumes:

```text
GET /api/v1/modules/load-plan/summary
GET /api/v1/modules/load-plan/packages
GET /api/v1/modules/load-plan/packages/{package_id}
```

## GUI Behavior

The screen uses shared components:

```text
- MetricGrid for registered package, source, catalog macro, and visible row counters;
- ModuleObjectList for selectable Load Plan packages;
- SelectedObjectPanel for selected package metadata;
- DetailList for the selected package load sequence.
```

The first selected package defaults to the first backend item. Selecting
another package updates the detail query through backend-owned ids.

## Safety

```text
- No client-specific sample data in tests or docs.
- No frontend-only package registration decisions.
- No frontend-only CSVUTIL, cutover readiness, or handoff actions.
- No local artifact path rendering.
- Package status, catalog macro, evidence references, artifact references, and load sequence come from backend contracts.
```

This slice intentionally keeps Load Plan read-only. CSVUTIL build, cutover
checklist, readiness, exports, and handoff actions can be wired later through
backend-owned available actions or explicit guarded endpoints.

## Validation

Commands executed:

```text
cd frontend
npm run test -- App.test.tsx
npm run lint
npm run test
npm run build
```
