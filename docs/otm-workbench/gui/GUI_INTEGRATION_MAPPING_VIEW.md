# GUI Integration Mapping View

**Status:** delivered  
**Branch:** `codex/gui-integration-mapping-view`  
**Scope:** first read-only, backend-backed Integration Mapping Studio screen.

## Purpose

Add a table-first Integration Mapping Studio view to the shared Workbench shell
without introducing module-specific layout patterns.

This slice keeps the frontend as a renderer of backend-owned mapping contracts:
definitions, transform types, payload artifact metadata, parsed schema
documents, and mapping rows.

## Backend Contracts Consumed

```text
GET /api/v1/modules/integration-mapping/transform-types
GET /api/v1/modules/integration-mapping/definitions
GET /api/v1/modules/integration-mapping/definitions/{definition_id}
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/payload-artifacts
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/schema-documents
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/mappings
```

The route remains activated by the backend navigation item:

```text
id: integration_mapping
path: /integration-mapping
```

## UI Pattern

The screen reuses the existing GUI foundation:

```text
PageHeader
MetricGrid
ModuleObjectList
SelectedObjectPanel
DetailList
StatusChip
```

Current panels:

```text
- Definition list
- Selected definition summary
- Payload artifact metadata
- Schema document metadata
- Mapping rows
```

## Safety Boundaries

This slice intentionally does not render raw payload content, local artifact
paths, manifest internals, client-specific data, or sample payload values.

It also does not expose validation, preview, spec generation, schema parsing,
create, edit, or delete actions. Those flows should be added only after the
backend provides explicit action contracts, lifecycle gates, permissions, and
evidence behavior for the GUI.

## Test Coverage

The GUI test suite now covers a synthetic Integration Mapping Studio contract:

```text
npm run test -- App.test.tsx
```

The fixture uses neutral synthetic data and verifies that the screen renders:

```text
- Integration Mapping Studio heading
- Definition code
- Payload artifact file name
- Schema root name
- Mapping target path
```

It also guards against prematurely showing spec generation controls.

## Next GUI Planning Notes

Future slices should stay table-first until the list/detail/review workflow is
stable. A visual canvas can be explored later, but should not replace backend
contracts for mappings, loops, joins, lookups, validation, preview, artifacts,
or audit evidence.
