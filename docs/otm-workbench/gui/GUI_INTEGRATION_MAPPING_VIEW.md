# GUI Integration Mapping View

**Status:** delivered  
**Branch:** `codex/gui-integration-mapping-view`  
**Scope:** staged, backend-backed Integration Mapping Studio workflow.

## Purpose

Add a staged Integration Mapping Studio workflow to the shared Workbench shell
without introducing module-specific layout patterns or stacking disconnected
authoring panels.

This slice keeps the frontend as a renderer of backend-owned mapping contracts:
definitions, transform types, payload artifact metadata, parsed schema
documents, mapping rows, validation/preview/spec actions, and generated
artifact metadata.

## Backend Contracts Consumed

```text
GET /api/v1/modules/integration-mapping/transform-types
GET /api/v1/modules/integration-mapping/definitions
GET /api/v1/modules/integration-mapping/definitions/{definition_id}
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/payload-artifacts
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/schema-documents
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/mappings
GET /api/v1/modules/integration-mapping/schema-documents/{schema_document_id}/nodes
POST /api/v1/modules/integration-mapping/definitions/{definition_id}/validate
POST /api/v1/modules/integration-mapping/definitions/{definition_id}/preview
POST /api/v1/modules/integration-mapping/definitions/{definition_id}/generate-spec
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/artifacts
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/artifacts/{artifact_id}/download
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
- Staged authoring navigation
- Systems and endpoints
- Definition authoring
- Payload and schema authoring
- Mapping, loop, join, and lookup authoring
- Selected definition summary
- Payload artifact metadata
- Schema document metadata
- Mapping rows
- Generated preview/spec artifacts
- Mapping-rule draft reset recovery
- Definition-switch recovery
```

## Safety Boundaries

This slice intentionally does not render raw payload content, local artifact
paths, manifest internals, client-specific data, sample payload values, or
external credentials.

Generated artifact rows expose only client-safe metadata and download through
guarded backend URLs. The frontend does not infer artifact paths, hashes,
ownership, or eligibility.

Definition switching is definition-workspace scoped. Selecting another
backend-owned definition clears payload draft fields, mapping/loop/join/lookup
drafts, download state, and stale feedback from the previously selected
definition. Generated artifacts, schemas, mappings, loops, joins, and lookups
continue to come from backend queries keyed by the selected definition id.

## Test Coverage

The GUI test suite now covers a synthetic Integration Mapping Studio contract:

```text
npm run qa:functional:integration-mapping
npm run qa:functional:integration-mapping:browser
```

The fixture uses neutral synthetic data and verifies that the screen renders:

```text
- Integration Mapping Studio heading
- Definition code
- Payload artifact file name
- Schema root name
- Mapping target path
- Staged workflow navigation
- Schema node selector usage
- Mapping-rule draft reset after mapping, loop, join, and lookup authoring
- Validate, preview, and generate-spec actions
- Generated artifact listing and guarded download
- Definition-switch recovery after artifact download/spec generation
```

It also guards against disconnected stacked authoring panels through the staged
workflow contract.

## Next GUI Planning Notes

Future slices should stay table-first until the list/detail/review workflow is
stable. A visual canvas can be explored later, but should not replace backend
contracts for mappings, loops, joins, lookups, validation, preview, artifacts,
or audit evidence.
