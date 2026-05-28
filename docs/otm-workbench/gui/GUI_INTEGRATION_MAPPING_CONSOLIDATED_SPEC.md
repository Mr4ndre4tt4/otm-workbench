# GUI Integration Mapping Studio Consolidated Specification

**Status:** draft for product review
**Date:** 2026-05-28
**Linear:** OTM-168
**Scope:** consolidated Integration Mapping Studio objective, current UI review,
browser findings, GUI information architecture, route map, click-by-click
operating model, and redesign direction.

## 0. Source Documents Consolidated

This document consolidates the Integration Mapping Studio direction currently
spread across GUI, QA, roadmap, schema discovery, and local integration
validation documents:

```text
docs/otm-workbench/gui/GUI_INTEGRATION_MAPPING_VIEW.md
docs/otm-workbench/gui/GUI_INTEGRATION_MAPPING_NDD_UI_QA.md
docs/otm-workbench/gui/GUI_INTEGRATION_MAPPING_VISUAL_QA_OTM79.md
docs/otm-workbench/gui/GUI_LOCAL_INTEGRATION_VALIDATION.md
docs/otm-workbench/gui/GUI_MODULE_EXPERIENCE_ROADMAP.md
docs/otm-workbench/discovery/OTM_26A_WSDL_XSD_DISCOVERY.md
outputs/integration-mapping-direction-intake/direction-brief.md
```

Those files remain valid supporting evidence. This consolidated spec is the
current navigation point for future Integration Mapping UX and implementation
work.

The external prototype prompts and architecture document reviewed on
2026-05-28 are treated as directional input only. They may contain
client/environment details and must be sanitized before any scenario, fixture,
test, screenshot, Figma frame, GitHub issue, or generated artifact becomes
project evidence.

## 1. Product Objective

Integration Mapping Studio should be the backend-first accelerator for
designing, validating, previewing, and governing integration mappings between
OTM payloads and external system payloads.

The enriched To-Be direction is an Integration Spec Compiler: the module should
not merely record field mappings, but compile backend-owned systems, schemas,
enrichment calls, mapping rules, validation findings, preview provenance, and
generated artifacts into a technical specification that a middleware developer
can implement with minimal rediscovery.

The module exists to help an implementation user:

```text
1. register integration systems and endpoints;
2. create an integration definition;
3. attach source, target, and intermediate payload samples or official schema
   roots;
4. browse source, target, and intermediate schema paths safely;
5. configure backend-owned enrichment steps for intermediate REST/SOAP calls;
6. author mappings, loops, joins, lookups, transforms, and response handling;
7. validate completeness and semantic correctness;
8. generate executable synthetic preview output with provenance;
9. generate a technical mapping spec;
10. review artifacts and evidence without exposing real customer data.
```

The module should feel like an accelerator because it reduces the work needed
to rebuild an integration such as:

```text
OTM PlannedShipment XML -> external delivery JSON
```

It should not feel like a raw form builder where the user has to understand the
backend model before they can do useful work.

## 2. Explicit Non-Goals

Integration Mapping Studio is not, for MVP0/MVP1:

```text
- a live integration runtime;
- a replacement for OIC, middleware, or transport orchestration;
- a place to store production credentials;
- a raw payload vault for customer data;
- a free-form document editor;
- a visual canvas that bypasses backend-owned rules;
- a frontend-owned mapping inference engine;
- a frontend-owned enrichment execution engine;
- a live caller of customer endpoints during MVP preview;
- a screen that renders every backend object at once.
```

The backend remains the source of truth for contracts, validation,
recommendations, action availability, preview execution, generated artifacts,
and evidence.

## 3. Current UI Review

Browser review of `/integration-mapping` found a technically strong but
operationally overloaded first slice.

Delivered strengths:

```text
- backend-backed systems, endpoints, definitions, payloads, schemas, mappings,
  loops, joins, join bindings, lookups, response handlers, validation, preview,
  spec, and artifacts exist;
- staged navigation exists;
- grouped executable review exists;
- synthetic NDD-like positive and negative QA paths exist;
- backend-owned suggestions and scoring exist;
- selected definition state clears enough stale draft state for the first MVP
  hardening round;
- raw payload values and local artifact paths are not exposed in the visible UI.
```

Current product and UX problems:

1. The route still combines system authoring, endpoint authoring, definition
   authoring, payload/schema authoring, rules, review, validation, preview,
   spec generation, artifact review, and definition list in one workspace.
2. The selected-object side panel carries too much operational weight. It is
   useful as context, but not as the main detail/review surface.
3. Systems and endpoints are shown as long repeated rows before the user has a
   clear integration definition story.
4. Mapping rules are still a dense vertical authoring surface. Mappings, loops,
   joins, join bindings, lookups, response handling, suggestions, and official
   paths compete for attention.
5. The grouped executable review is valuable, but it is embedded above authoring
   forms instead of being a dedicated review step.
6. The "Definitions list" is a stage inside an active definition workflow. This
   is conceptually backwards: list/search belongs to the hub/library route.
7. Search, filters, and definition management are too weak for 128 definitions.
8. Important actions such as validate, preview, generate spec, remove mapping,
   and create synthetic samples are scattered between main stage and side panel.
9. The stage names are implementation-oriented. A user needs an operating story:
   choose definition, define contract, load schemas, map fields, validate,
   preview, generate spec.
10. The UI proves that the backend can do the work, but it still asks the user
    to assemble the mental model from many panels.
11. Enrichment calls are not yet a first-class product concept. Intermediate
    payloads, enrichment steps, substeps, enriched virtual fields, and
    enrichment readiness need explicit contracts before the module can satisfy
    the Integration Spec Compiler direction.

Product conclusion:

```text
The current Integration Mapping Studio is a credible backend functional slice,
but it is not yet a genuinely good integration accelerator. It needs route-level
storytelling, focused workspaces, searchable schema/path experiences, and a
dedicated review/preview/spec journey.
```

## 4. Design Decision

Replace the single heavy staged screen with a route-level integration
workspace.

The new IA should be:

```text
/integration-mapping
  Integration definitions hub

/integration-mapping/definitions/new
  Create integration definition

/integration-mapping/definitions/:definitionId
  Definition cockpit

/integration-mapping/definitions/:definitionId/systems
  Systems and endpoints used by this definition

/integration-mapping/definitions/:definitionId/schemas
  Payload samples and official schema roots

/integration-mapping/definitions/:definitionId/enrichment
  Intermediate calls and enriched field publication

/integration-mapping/definitions/:definitionId/mapping
  Mapping workspace

/integration-mapping/definitions/:definitionId/mapping/:ruleId
  Mapping rule detail/edit

/integration-mapping/definitions/:definitionId/rules
  Loops, joins, lookups, transforms, and response handling

/integration-mapping/definitions/:definitionId/review
  Completeness and executable review

/integration-mapping/definitions/:definitionId/preview
  Synthetic preview execution and provenance

/integration-mapping/definitions/:definitionId/spec
  Generated spec review

/integration-mapping/definitions/:definitionId/artifacts
  Generated artifacts and guarded downloads

/integration-mapping/systems
  Reusable integration systems library

/integration-mapping/systems/:systemId
  Reusable system detail
```

Every detail, edit, copy, remove, archive, and generated-result route must have
a visible `Back` action.

## 5. Global UX Rules

1. `/integration-mapping` is a library/hub, not an authoring workbench.
2. A definition detail route is the primary object cockpit.
3. System and endpoint authoring must be separated from field mapping.
4. Payload/schema setup must be separated from mapping rules.
5. Enrichment steps must be a dedicated route between schema setup and mapping
   authoring, because they publish virtual source fields and affect preview,
   readiness, and generated specs.
6. Mapping rules must have focused editors, not one long page with every rule
   type.
7. Review, validation, preview, and spec generation must be dedicated steps.
8. Destructive actions such as remove mapping, delete draft, or retire a
   definition must open a dedicated confirmation route or modal with backend
   impact summary.
9. Generated artifacts must use guarded backend downloads only.
10. Suggestions must remain backend-owned and explain confidence/reason.
11. Official OTM paths must come from Catalog/Core schema-pack contracts when
    available; sample payload schemas are complementary, not the only source.
12. No real client payload, CNPJ, CPF, endpoint credential, local file path, or
    production identifier should appear in fixtures, docs, screenshots, or
    UI seeds.

## 6. Screen: `/integration-mapping`

### Purpose

Help the user find or start an integration definition.

### Backend Loads

```text
GET /api/v1/modules/integration-mapping/definitions?filters...
GET /api/v1/modules/integration-mapping/summary
GET /api/v1/modules/integration-mapping/filter-options
GET /api/v1/platform/navigation
```

### Main Content

```text
- searchable definitions table;
- saved views: All, Drafts, Needs validation, Preview ready, Spec generated,
  Recently updated;
- summary metrics that answer operational questions, not decorative counts;
- primary action: New definition;
- secondary action: Systems library;
- row actions: Open, Copy, Retire/Delete draft, Generate new version.
```

### Searchable Header Fields

Each searchable field should support:

```text
begins with
contains
one of
not one of
```

Comma-separated values are used for `one of` and `not one of`.

Recommended searchable fields:

```text
definition_code
definition_name
client_code
project_code
source_system_code
target_system_code
source_format
target_format
scenario_pack
status
owner
version
tags
otm_version
schema_pack_code
has_preview_artifact
has_generated_spec
updated_by
updated_at
description
```

### Clicks

| Click | Opens |
|---|---|
| `New definition` | `/integration-mapping/definitions/new` |
| definition row | `/integration-mapping/definitions/:definitionId` |
| `Systems library` | `/integration-mapping/systems` |
| `Copy` | `/integration-mapping/definitions/:definitionId/copy` |
| `Retire/Delete draft` | `/integration-mapping/definitions/:definitionId/retire` |
| filter chip | updates backend query and URL state |
| saved view | updates backend query and URL state |

### What Must Not Be Here

```text
- payload text areas;
- mapping forms;
- joins/lookups forms;
- artifact raw content;
- selected-object side panel as the primary detail surface.
```

## 7. Screen: `/integration-mapping/definitions/new`

### Purpose

Create the integration header and choose whether the definition starts from a
scenario pack, uploaded samples, or official schema roots.

### Backend Loads

```text
GET /api/v1/modules/integration-mapping/create-options
GET /api/v1/modules/integration-mapping/scenario-packs
GET /api/v1/catalog/schema-packs?recommended_module=integration_mapping
GET /api/v1/modules/integration-mapping/systems?status=active
```

### Fields

```text
definition_code
definition_name
client_code
project_code
source_system_id
target_system_id
source_format
target_format
scenario_pack
otm_version
schema_pack_id
description
tags
```

### Actions

| Action | Backend execution | Result |
|---|---|---|
| `Create definition` | `POST /definitions` | navigate to definition cockpit |
| `Create from scenario pack` | `POST /definitions` with scenario pack | preloads required target checklist and sample-safe starter metadata |
| `Cancel` | none | back to hub |

## 8. Screen: `/integration-mapping/definitions/:definitionId`

### Purpose

Give the user the cockpit for one integration definition.

### Backend Loads

```text
GET /api/v1/modules/integration-mapping/definitions/{definition_id}
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/readiness
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/activity
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/available-actions
```

### Main Content

```text
- definition header and status;
- next recommended action from backend;
- readiness cards: contract, schemas, enrichment, mappings, required targets,
  preview, spec;
- recent artifacts and validation summaries;
- route cards to Systems, Schemas, Enrichment, Mapping, Rules, Review,
  Preview, Spec, Artifacts;
- activity timeline.
```

### Clicks

| Click | Opens |
|---|---|
| `Back` | `/integration-mapping` preserving filters |
| `Systems & endpoints` | `/integration-mapping/definitions/:definitionId/systems` |
| `Payloads & schemas` | `/integration-mapping/definitions/:definitionId/schemas` |
| `Enrichment pipeline` | `/integration-mapping/definitions/:definitionId/enrichment` |
| `Mapping workspace` | `/integration-mapping/definitions/:definitionId/mapping` |
| `Rules` | `/integration-mapping/definitions/:definitionId/rules` |
| `Review` | `/integration-mapping/definitions/:definitionId/review` |
| `Preview` | `/integration-mapping/definitions/:definitionId/preview` |
| `Spec` | `/integration-mapping/definitions/:definitionId/spec` |
| `Artifacts` | `/integration-mapping/definitions/:definitionId/artifacts` |
| `Edit header` | `/integration-mapping/definitions/:definitionId/edit` |
| `Copy definition` | `/integration-mapping/definitions/:definitionId/copy` |
| `Retire/Delete draft` | `/integration-mapping/definitions/:definitionId/retire` |

## 9. Screen: Systems And Endpoints

### Purpose

Let the user confirm the source and target system contracts for this
definition.

### Route

```text
/integration-mapping/definitions/:definitionId/systems
```

### Backend Loads

```text
GET /api/v1/modules/integration-mapping/definitions/{definition_id}
GET /api/v1/modules/integration-mapping/systems?status=active
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/endpoints
GET /api/v1/modules/integration-mapping/system-types
GET /api/v1/modules/integration-mapping/http-methods
```

### Main Content

```text
- selected source system;
- selected target system;
- endpoints used by this definition;
- reusable system search;
- endpoint detail table.
```

### Actions

| Action | Backend execution | Result |
|---|---|---|
| `Attach source system` | `PATCH /definitions/{id}` | updates source system |
| `Attach target system` | `PATCH /definitions/{id}` | updates target system |
| `Create endpoint` | `POST /systems/{system_id}/endpoints` | endpoint appears in table |
| `Edit endpoint` | `PATCH /endpoints/{endpoint_id}` | row updates |
| `Detach endpoint` | `DELETE /definitions/{id}/endpoints/{endpoint_id}` or status action | backend impact summary required |

## 10. Screen: Payloads And Schemas

### Purpose

Let the user attach source, target, and intermediate samples or official schema
roots and then inspect schema readiness.

### Route

```text
/integration-mapping/definitions/:definitionId/schemas
```

### Backend Loads

```text
GET /api/v1/modules/integration-mapping/definitions/{definition_id}
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/payload-artifacts
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/schema-documents
GET /api/v1/catalog/schema-roots?recommended_module=integration_mapping
GET /api/v1/catalog/schema-roots/{schema_root_id}/paths?filters...
```

### Main Content

```text
- source contract panel;
- target contract panel;
- intermediate response schema set;
- payload sample cards;
- official schema root cards;
- schema parse status;
- searchable tree/path browser;
- node metadata: path, type, cardinality, repeatability, required flag,
  documentation basis, source file/schema pack.
```

### Actions

| Action | Backend execution | Result |
|---|---|---|
| `Upload/paste source sample` | `POST /payload-artifacts` | creates artifact and schema document |
| `Upload/paste target sample` | `POST /payload-artifacts` | creates artifact and schema document |
| `Upload/paste intermediate sample` | `POST /payload-artifacts` | creates intermediate artifact and schema document |
| `Attach official source root` | `POST /definitions/{id}/schema-roots` | official path browser available |
| `Attach official target root` | `POST /definitions/{id}/schema-roots` | official path browser available |
| `Reparse schema` | backend parse job/action | schema readiness refreshed |
| `Remove sample` | guarded backend action | impact summary and stale mapping blocker |

## 11. Screen: Enrichment Pipeline

### Purpose

Let the user define intermediate calls that enrich the source payload before
final target mapping. Enrichment is not a live runtime in MVP; it is a
backend-owned specification of calls, keys, response extraction, error policy,
and virtual fields that mapping, review, preview, and generated spec can trust.

### Route

```text
/integration-mapping/definitions/:definitionId/enrichment
```

### Backend Loads

```text
GET /api/v1/modules/integration-mapping/definitions/{definition_id}
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/enrichment-steps
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/enriched-fields
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/enrichment-readiness
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/payload-artifacts?direction=intermediate
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/schema-documents?direction=intermediate
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/endpoints
```

### Main Content

```text
- ordered enrichment step list;
- step status, type, endpoint, key binding, and policy summary;
- substep list for chained calls under the same logical step;
- loop-scoped enrichment indicator for collection-based enrichment;
- response schema selector and response extraction table;
- enriched field publication table;
- readiness blockers and warnings owned by backend validation.
```

### Data Concepts

```text
EnrichmentStep
  id
  definition_id
  name
  step_order
  step_type: SINGLE | CHAIN | LOOP
  endpoint_id
  loop_source_path
  loop_filter_expression
  key_template
  key_source_fields
  response_schema_document_id
  on_empty_response: FAIL | WARN | USE_DEFAULT | SKIP
  on_error: FAIL | WARN | SKIP
  status

EnrichmentSubStep
  id
  enrichment_step_id
  substep_order
  endpoint_id
  request_path_template
  request_key_bindings
  response_schema_document_id
  response_field_mappings
  status

EnrichedField
  id
  definition_id
  enrichment_step_id
  enrichment_substep_id
  name
  data_type
  cardinality: SCALAR | ARRAY | LOOP_SCOPED
  response_path
  fallback_policy
  sample_value_redacted
  source_trace
```

### Actions

| Action | Backend execution | Result |
|---|---|---|
| `Create enrichment step` | `POST /definitions/{id}/enrichment-steps` | draft step appears in ordered list |
| `Edit enrichment step` | `PATCH /enrichment-steps/{step_id}` | backend validates key/schema references |
| `Add substep` | `POST /enrichment-steps/{step_id}/substeps` | chained call appears under owning step |
| `Publish enriched field` | backend response mapping action | enriched field becomes available to mapping |
| `Validate step` | `POST /enrichment-steps/{step_id}/validate` | blockers/warnings refresh |
| `Reorder steps` | `POST /definitions/{id}/enrichment-steps/reorder` | execution/spec order updates |
| `Remove step` | guarded delete/status endpoint | impact summary lists affected mappings |

### Rules

```text
- enriched fields are read-only outputs of enrichment configuration;
- frontend may render suggested fields, but backend owns publication and status;
- loop-scoped enriched fields cannot be used in header mappings without an
  explicit aggregation/selection rule;
- source paths used for key bindings must be checked against source schemas or
  official schema roots;
- response paths must be checked against intermediate response schemas;
- generated spec must include enrichment calls as middleware activities with
  request keys, response extraction, fallback policy, and failure behavior.
```

## 12. Screen: Mapping Workspace

### Purpose

Let the user map fields between source and target without overwhelming them
with every rule type at once.

### Route

```text
/integration-mapping/definitions/:definitionId/mapping
```

### Backend Loads

```text
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/mappings
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/mapping-suggestions
GET /api/v1/modules/integration-mapping/schema-documents/{schema_document_id}/nodes
GET /api/v1/catalog/schema-roots/{schema_root_id}/paths?filters...
GET /api/v1/modules/integration-mapping/transform-types
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/required-targets
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/enriched-fields
```

### Layout

```text
Left: source path browser and enriched fields
Center: mapping table grouped by target section
Right: target path browser and selected target requirement
Bottom/Drawer: selected rule editor
```

### Clicks

| Click | Opens |
|---|---|
| source path | selects source path for draft mapping |
| target path | selects target path for draft mapping |
| mapping row | `/integration-mapping/definitions/:definitionId/mapping/:ruleId` |
| suggestion row | fills a local review set, not an immediate mapping |
| required target row | filters mapping table to that target |
| `Add direct mapping` | opens focused rule editor |
| `Add transform mapping` | opens focused transform editor |
| `Bulk apply selected suggestions` | backend all-or-nothing creation |

### Actions

| Action | Backend execution | Result |
|---|---|---|
| `Load suggestions` | `GET /mapping-suggestions` | backend confidence/reason displayed |
| `Create mapping` | `POST /mappings` or bulk endpoint | row appears and review readiness changes |
| `Edit mapping` | `PATCH /mappings/{mapping_id}` | rule detail updates |
| `Remove mapping` | guarded delete/status endpoint | requires impact summary |
| `Validate selected target` | backend validation scoped to target path | row blockers update |

## 13. Screen: Rule Detail/Edit

### Purpose

Edit one mapping rule with enough room to explain source, target, transform,
scope, and provenance.

### Route

```text
/integration-mapping/definitions/:definitionId/mapping/:ruleId
```

### Required Sections

```text
- Back to mapping workspace;
- rule header and status;
- source context;
- target context;
- transform configuration;
- alias/loop scope;
- validation blockers;
- preview provenance when available;
- audit/activity for this rule.
```

### Actions

| Action | Backend execution | Result |
|---|---|---|
| `Save` | `PATCH /mappings/{mapping_id}` | stay on detail with success feedback |
| `Validate rule` | scoped validation endpoint | blockers and warnings refresh |
| `Remove` | guarded delete/status endpoint | confirmation route/modal, then back |
| `Duplicate` | backend copy endpoint | new draft rule detail |

## 14. Screen: Rules

### Purpose

Author structural and non-field rules separately from field mapping.

### Route

```text
/integration-mapping/definitions/:definitionId/rules
```

### Rule Families

```text
loops
joins
join bindings
lookups
aggregations
response handling
constants/defaults
date and qualifier transform presets
```

### UX Pattern

Each family is a tab or segmented section with:

```text
- current rules table;
- Create rule action;
- focused detail route/drawer;
- validation state;
- impact on required targets and preview.
```

Do not render every loop/join/lookup/response form in one long vertical page.

## 15. Screen: Review

### Purpose

Tell the user whether the integration definition is complete enough to preview
or generate a spec.

### Route

```text
/integration-mapping/definitions/:definitionId/review
```

### Backend Loads

```text
POST /api/v1/modules/integration-mapping/definitions/{definition_id}/validate
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/review
```

### Main Content

```text
- Header group;
- target collections such as Entregas[];
- required target checklist;
- unmapped target fields;
- duplicate target mappings;
- invalid paths;
- alias and loop-scope blockers;
- transform config blockers;
- lookup blockers;
- join semantic blockers;
- response handling blockers;
- readiness: specification_ready and preview_executable.
```

### Actions

| Action | Backend execution | Result |
|---|---|---|
| `Run validation` | backend validation | readiness and blockers refresh |
| `Open blocker` | navigates to the owning route/detail |
| `Continue to preview` | route navigation if preview executable | `/preview` |
| `Continue to spec` | route navigation if specification ready | `/spec` |

## 16. Screen: Preview

### Purpose

Prove that the mapping produces expected synthetic output and explain field
provenance.

### Route

```text
/integration-mapping/definitions/:definitionId/preview
```

### Backend Loads/Actions

```text
POST /api/v1/modules/integration-mapping/definitions/{definition_id}/preview
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/artifacts?type=preview
```

### Main Content

```text
- preview readiness;
- generated synthetic target summary;
- field provenance table;
- warnings and blockers;
- artifact metadata and guarded download.
```

Raw payload preview should be a documented exception with safe redaction. The
default view should be structured summary plus provenance, not a giant payload
dump.

## 17. Screen: Spec

### Purpose

Generate and review a durable technical mapping specification.

### Route

```text
/integration-mapping/definitions/:definitionId/spec
```

### Backend Loads/Actions

```text
POST /api/v1/modules/integration-mapping/definitions/{definition_id}/generate-spec
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/artifacts?type=spec
```

### Main Content

```text
- spec readiness;
- included systems/endpoints;
- source/target schema summary;
- mapping inventory;
- transform inventory;
- loops/joins/lookups;
- response handling;
- required target coverage;
- generated artifact metadata and guarded download.
```

## 18. Screen: Artifacts

### Purpose

Review generated preview/spec artifacts and download them through guarded
backend endpoints.

### Route

```text
/integration-mapping/definitions/:definitionId/artifacts
```

### Backend Loads

```text
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/artifacts
GET /api/v1/modules/integration-mapping/definitions/{definition_id}/artifacts/{artifact_id}/download
```

### Main Content

```text
- generated artifact list;
- artifact type, created at, created by, hash/checksum, status;
- linked validation or preview run;
- guarded download action;
- Evidence Hub archive action when eligible.
```

## 19. Systems Library

### Purpose

Maintain reusable integration systems separately from mapping work.

### Routes

```text
/integration-mapping/systems
/integration-mapping/systems/new
/integration-mapping/systems/:systemId
/integration-mapping/systems/:systemId/edit
```

The system library should support search/filter by:

```text
system_code
system_name
system_type
status
base_url_host_safe_label
owner
tags
description
```

Endpoint credentials must never be rendered or stored as raw UI fields.

## 20. Backend Contract Gaps

The current backend is strong enough for the first functional slice, but the
redesign needs explicit route-friendly contracts:

```text
GET /definitions summary and paginated filtered list
GET /definitions/filter-options
GET /definitions/{id}/cockpit
GET /definitions/{id}/available-actions
GET /definitions/{id}/readiness
GET /definitions/{id}/review
GET /definitions/{id}/required-targets
GET /definitions/{id}/activity
GET /definitions/{id}/enrichment-steps
GET /definitions/{id}/enriched-fields
GET /definitions/{id}/enrichment-readiness
POST /definitions/{id}/copy
POST /definitions/{id}/retire or DELETE draft with impact summary
PATCH /definitions/{id}
POST /definitions/{id}/enrichment-steps
POST /definitions/{id}/enrichment-steps/reorder
PATCH /enrichment-steps/{id}
POST /enrichment-steps/{id}/substeps
PATCH /enrichment-substeps/{id}
POST /enrichment-steps/{id}/validate
DELETE or retire enrichment step with impact summary
PATCH /mappings/{id}
POST /mappings/{id}/copy
DELETE or retire mapping with impact summary
GET /systems filtered list
PATCH /systems/{id}
```

Where these already exist under different names, the GUI should consume the
backend contract rather than invent local readiness logic.

## 21. QA Journeys

Required browser/UI QA:

```text
1. create synthetic definition from scenario pack;
2. attach source and target samples;
3. attach intermediate response samples;
4. attach official OTM schema root;
5. search source, target, and intermediate paths;
6. create enrichment step and substep from safe synthetic endpoint metadata;
7. publish an enriched field and confirm it appears in the mapping source
   browser;
8. apply backend suggestions to review set;
9. bulk create selected suggestions;
10. create direct mapping manually;
11. create loop and loop-scoped mapping;
12. create mapping from an enriched field;
13. create multi-hop join binding;
14. create lookup;
15. create response handler;
16. validate and open blocker from review;
17. fix enrichment blocker and validate again;
18. preview synthetic target output and inspect enrichment provenance;
19. generate spec and confirm enrichment sequence is documented;
20. download guarded artifact;
21. leave and return to each route without stale state;
22. switch definitions while drafts are dirty;
23. remove enrichment step and confirm dependent mapping/readiness impact;
24. remove mapping and confirm dependent readiness changes;
25. try invalid alias/path and confirm blocked preview;
26. verify no raw customer payload, credential, endpoint, CNPJ/CPF, or local
   path is exposed.
```

Visual QA:

```text
- desktop and mobile route fit;
- light/dark/system theme;
- long OTM path wrapping/truncation;
- high-volume definition list;
- empty state for no definitions;
- no-result state for search;
- validation blocked state;
- disabled-by-permission state;
- generated artifact success state.
```

## 22. Implementation Slices

Recommended implementation order:

```text
1. Hub and filtered definition library.
2. Definition cockpit route with backend next action/readiness.
3. Create/edit/copy/retire definition routes.
4. Systems/endpoints route separation.
5. Payload/schema route with searchable tree/path browser and intermediate
   response schema support.
6. Enrichment domain/API contracts with steps, substeps, enriched fields,
   readiness, and impact summaries.
7. Enrichment route shell with list/detail and backend validation states.
8. Mapping workspace with source/target browser, enriched fields, and
   selected-suggestion review.
9. Rule family routes for loops, joins, lookups, response handlers.
10. Dedicated review route.
11. Dedicated preview route with enrichment provenance.
12. Dedicated spec/artifacts routes with enrichment sequence in generated
    spec.
13. Browser QA for sanitized synthetic scenario across routes.
```

## 23. Acceptance Criteria

The module can be considered product-ready for this class of integration only
when:

```text
- a user can start from the hub and understand the next step without knowing
  the backend table/model;
- each screen has one primary job;
- the NDD-like synthetic integration can be recreated through the UI;
- intermediate enrichment calls can be specified without live customer endpoint
  execution;
- enriched fields can be used in mappings with backend-owned provenance;
- preview proves executable target output, not only metadata;
- validation explains blockers and links to the place to fix them;
- generated spec explains trigger, source/target contracts, enrichment
  sequence, mappings, loops, response handling, and implementation notes;
- generated spec and preview artifacts are downloadable through guarded
  backend endpoints;
- out-of-order navigation and definition switching do not leave stale drafts;
- docs, tests, Linear, and GitHub all point to this spec;
- no real client data is used.
```

## 24. Decision Summary

The current Integration Mapping Studio should not be treated as final UX. It is
a strong backend demonstration and functional QA surface. The next step is to
turn it into a route-based integration accelerator where each screen advances a
clear story:

```text
Find definition -> define contract -> load schemas -> configure enrichment ->
map fields -> author rules -> validate -> preview -> generate spec -> review
artifacts.
```
