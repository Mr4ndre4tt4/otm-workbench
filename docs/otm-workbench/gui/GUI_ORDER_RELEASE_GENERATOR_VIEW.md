# GUI Order Release Generator View

**Status:** implemented
**Branch:** `codex/gui-order-release-generator-view`

## Objective

Add the first backend-backed Order Release Generator screen using the shared GUI
foundation.

Order Release Generator now renders template list, selected template metadata,
required columns, optional columns, and defaults from backend contracts instead
of the generic module placeholder.

## Backend Contracts

The GUI consumes:

```text
GET /api/v1/modules/order-release-generator/templates
```

The backend currently exposes batch detail by id, but not a batch list endpoint,
so this first GUI slice starts with templates only.

## GUI Behavior

The screen uses shared components:

```text
- MetricGrid for template, required column, optional column, and default counters;
- ModuleObjectList for selectable Order Release templates;
- SelectedObjectPanel for selected template metadata;
- DetailList for required columns;
- DetailList for optional columns and defaults.
```

The first selected template defaults to the first backend item. Selecting
another template updates the selected panel from the backend-owned template
list.

## Safety

```text
- No client-specific sample data in tests or docs.
- No frontend-only batch creation decisions.
- No XML preview, XML artifact generation, or OTM submit actions.
- No local artifact path rendering.
- Template status, macro object linkage, columns, and defaults come from backend contracts.
```

This slice intentionally keeps Order Release Generator read-only. Batch import,
batch detail navigation, XML preview, XML artifact generation, and OTM submit
controls can be wired later through backend-owned available actions or explicit
guarded endpoints.

## Validation

Commands executed:

```text
cd frontend
npm run test -- App.test.tsx
npm run lint
npm run test
npm run build
```
