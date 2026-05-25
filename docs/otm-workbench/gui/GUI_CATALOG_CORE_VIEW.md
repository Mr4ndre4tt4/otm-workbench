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
- DetailList for load plan dependency/target steps;
- Catalog validation reset action to restore the default synthetic table,
  column, and reference fields and clear stale validation results.
- Macro-object switch recovery clears route-session table, column, reference,
  error, and running validation results before loading the newly selected
  backend macro object.
```

The first selected macro object defaults to the first backend item. Selecting
another macro object updates detail, table, and load plan queries through
backend-owned codes and clears validation results that belonged to the previous
macro object context.

## Safety

```text
- No client-specific sample data in tests or docs.
- No frontend-only catalog import decisions.
- No frontend-only table, column, or reference validation actions.
- No data dictionary file path rendering.
- Macro status, table eligibility, validation state, and load plan sequence come from backend contracts.
```

This slice keeps Catalog Core metadata read-only while exposing guarded
backend-owned table, column, and reference validation endpoints. The reset
action is UI-local recovery only; validation truth remains backend-owned.

## Validation

Commands executed:

```text
cd frontend
npm run test -- AppFunctionalCatalog.test.tsx
npm run qa:functional:catalog:browser
npm run lint
npm run build
python -m pytest tests/test_catalog_core.py -q
```
