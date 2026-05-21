# GUI Master Data View

**Status:** implemented
**Branch:** `codex/gui-master-data-view`

## Objective

Add the first backend-backed Data Factory / Master Data screen using the shared
GUI foundation.

Master Data now renders template list, selected template metadata, sheets, and
fields from backend contracts instead of the generic module placeholder.

## Backend Contracts

The GUI consumes:

```text
GET /api/v1/modules/master-data/templates
GET /api/v1/modules/master-data/templates/{template_code}
```

## GUI Behavior

The screen uses shared components:

```text
- MetricGrid for template, target table, sheet, and field counters;
- ModuleObjectList for selectable Master Data templates;
- SelectedObjectPanel for selected template metadata;
- DetailList for template sheets;
- DetailList for template fields.
```

The first selected template defaults to the first backend item. Selecting
another template updates the detail query through backend-owned template codes.

## Safety

```text
- No client-specific sample data in tests or docs.
- No frontend-only template validation decisions.
- No workbook build, upload, parse, map, output, CSV build, or CSV package export actions.
- No local artifact path rendering.
- Template status, sheets, fields, target tables, and catalog macro linkage come from backend contracts.
```

This slice intentionally keeps Master Data read-only. Template validation,
workbook generation, workbook upload, batch mapping, output generation, CSV
generation, and package export can be wired later through backend-owned
available actions or explicit guarded endpoints.

## Validation

Commands executed:

```text
cd frontend
npm run test -- App.test.tsx
npm run lint
npm run test
npm run build
```
