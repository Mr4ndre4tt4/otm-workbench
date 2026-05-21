# GUI Catalog Core View

**Status:** implemented
**Branch:** `codex/gui-catalog-core-view`

## Objective

Add the first backend-backed OTM Catalog Core screen using the shared GUI
foundation.

Catalog Core now renders macro objects, selected macro metadata, linked tables,
and load plan steps from backend contracts instead of the generic module
placeholder.

## Backend Contracts

The GUI consumes:

```text
GET /api/v1/catalog/macro-objects
GET /api/v1/catalog/macro-objects/{macro_object_code}
GET /api/v1/catalog/macro-objects/{macro_object_code}/tables
GET /api/v1/catalog/macro-objects/{macro_object_code}/load-plan
```

## GUI Behavior

The screen uses shared components:

```text
- MetricGrid for macro object, CSVUTIL, cutover, and validated table counters;
- ModuleObjectList for selectable catalog macro objects;
- SelectedObjectPanel for selected macro object metadata;
- DetailList for linked OTM tables;
- DetailList for load plan dependency/target steps.
```

The first selected macro object defaults to the first backend item. Selecting
another macro object updates detail, table, and load plan queries through
backend-owned codes.

## Safety

```text
- No client-specific sample data in tests or docs.
- No frontend-only catalog import decisions.
- No frontend-only table, column, or reference validation actions.
- No data dictionary file path rendering.
- Macro status, table eligibility, validation state, and load plan sequence come from backend contracts.
```

This slice intentionally keeps Catalog Core read-only. Dictionary import,
table validation, column validation, and reference validation can be wired later
through backend-owned available actions or explicit guarded endpoints.

## Validation

Commands executed:

```text
cd frontend
npm run test -- App.test.tsx
npm run lint
npm run test
npm run build
```
