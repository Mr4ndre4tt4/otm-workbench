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
documents, Catalog-owned source/target schema path options, mapping rows,
validation/preview/spec actions, and generated artifact metadata. Validation
readiness is rendered from the backend contract, separating definitions that are
specification-ready from definitions that are executable in preview.

## Backend Contracts Consumed

```text
GET /api/v1/modules/integration-mapping/transform-types
GET /api/v1/modules/integration-mapping/definitions
GET /api/v1/modules/integration-mapping/definitions/{definition_id}
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/payload-artifacts
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/schema-documents
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/mappings
POST /api/v1/modules/integration-mapping/definitions/{definition_id}/mappings/bulk
GET /api/v1/modules/integration-mapping/schema-documents/{schema_document_id}/nodes
GET /api/v1/catalog/schema-roots?schema_guidance_role=ENVELOPE_ONLY
GET /api/v1/catalog/schema-roots?schema_guidance_role=MACRO_OBJECT
GET /api/v1/catalog/schema-roots/{schema_root_id}/paths
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
NextActionPanel
StatusChip
```

Current panels:

```text
- Staged authoring navigation
- Systems and endpoints
- Definition authoring
- Payload and schema authoring
- Mapping, loop, join, and lookup authoring
- Grouped executable review for Header, Entregas loop, Joins, Lookups,
  Transforms, Aggregations, and Response Handling
- Selected definition summary
- Payload artifact metadata
- Schema document metadata
- Mapping rows
- Specification readiness and preview executability
- Generated preview/spec artifacts
- Mapping-rule draft reset recovery
- Definition-switch recovery
- Next action panel for the selected definition and active workflow stage
```

## Safety Boundaries

This slice intentionally does not render raw payload content, local artifact
paths, manifest internals, client-specific data, sample payload values, or
external credentials.

Generated artifact rows expose only client-safe metadata and download through
guarded backend URLs. The frontend does not infer artifact paths, hashes,
ownership, or eligibility.

Validation readiness is not inferred by the GUI. The side panel only renders
`readiness.specification_ready`, `readiness.preview_executable`,
`specification_blockers`, and `preview_blockers` returned by backend
validation, preview, or spec generation.

Definition switching is definition-workspace scoped. Selecting another
backend-owned definition clears payload draft fields, mapping/loop/join/lookup
drafts, download state, stale readiness, and stale feedback from the previously
selected definition. Generated artifacts, schemas, mappings, loops, joins, and
lookups continue to come from backend queries keyed by the selected definition
id.

The `NextActionPanel` remains an informational renderer. Until Integration
Mapping exposes a dedicated `available_actions` contract, it derives a small
temporary recommendation from backend-returned definition, payload/schema,
mapping, validation, and generated artifact state. It does not execute actions
or invent permission/readiness decisions.

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
- Grouped executable review visibility after mapping, loop, join, and lookup
  authoring
- Mapping-rule draft reset after mapping, loop, join, and lookup authoring
- Validate, preview, and generate-spec actions
- Specification readiness and preview executability after validation
- Generated artifact listing and guarded download
- Next action progression from blocked definition selection through payloads,
  mappings, validation, preview, spec generation, and artifact review
- Definition-switch recovery after artifact download/spec generation, including
  stale readiness clearance
```

It also guards against disconnected stacked authoring panels through the staged
workflow contract.

## Next GUI Planning Notes

Future slices should stay table-first until the list/detail/review workflow is
stable. A visual canvas can be explored later, but should not replace backend
contracts for mappings, loops, joins, lookups, validation, preview, artifacts,
or audit evidence.

## NDD-like UI QA Follow-up

A 2026-05-25 browser QA attempted to recreate a synthetic version of the
PlannedShipment XML to external delivery JSON scenario.

Outcome:

```text
- The current UI can create the metadata/specification path.
- It cannot yet prove a complete functional transformation because preview is
  metadata-only.
- Complex OTM XML paths need searchable tree pickers and grouped review, not
  plain selects.
- Joins, loops, lookups, transforms, and required target fields need semantic
  validation before this module can be considered a strong accelerator.
- `OTM-144` delivered the first grouped review surface, which makes the
  accelerator gaps explicit without claiming multi-hop joins or aggregation
  execution are already solved.
```

Detailed notes:

```text
docs/otm-workbench/gui/GUI_INTEGRATION_MAPPING_NDD_UI_QA.md
```
