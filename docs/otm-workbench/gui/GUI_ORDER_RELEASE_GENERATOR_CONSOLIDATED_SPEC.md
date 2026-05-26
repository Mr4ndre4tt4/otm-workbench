# GUI Order Release Generator Consolidated Specification

**Status:** draft for product review
**Date:** 2026-05-26
**Linear:** OTM-169
**Scope:** consolidated Order Release Generator objective, current UI review,
browser findings, GUI information architecture, route map, click-by-click
operating model, and redesign direction.

## 0. Source Documents Consolidated

This document consolidates the Order Release Generator direction currently
spread across GUI, roadmap, backend contract, and OTM schema discovery
documents:

```text
docs/otm-workbench/gui/GUI_ORDER_RELEASE_GENERATOR_VIEW.md
docs/otm-workbench/gui/GUI_MODULE_EXPERIENCE_ROADMAP.md
docs/otm-workbench/gui/GUI_GENERAL_SOLUTION_QA_2026_05_25.md
docs/otm-workbench/discovery/OTM_26A_WSDL_XSD_DISCOVERY.md
```

Those files remain valid supporting evidence. This consolidated spec is the
current navigation point for future Order Release Generator UX and
implementation work.

## 1. Product Objective

Order Release Generator should be the backend-first accelerator for creating
valid, synthetic, governed OTM Order Release XML/DBXML artifacts from reusable
business-friendly templates.

The module exists to help an implementation user:

```text
1. find or create an Order Release template;
2. understand the template fields, defaults, and official OTM XML target;
3. create a batch of synthetic order release rows;
4. validate the batch before generation;
5. preview the generated XML structure;
6. generate a guarded XML/DBXML artifact;
7. download or archive the generated artifact;
8. inspect direct OTM submit readiness while keeping submit guarded until
   connection, credentials, audit, and capability governance are ready.
```

The module should be especially useful during testing, CRP preparation, and
technical validation where users need repeatable Order Release payloads without
hand-writing XML.

## 2. Core Story

The original story is valid:

```text
Templates -> Batch -> Preview -> Artifact -> Submit
```

The UX issue is not the lifecycle itself. The issue is that the current route
renders the lifecycle, template authoring, versioning, template list, active
batch, recent batches, XML preview, artifact generation, and submit guard in one
shared workspace.

The product story should become:

```text
Choose template -> create batch -> validate rows -> preview XML -> generate
artifact -> review/download/archive -> inspect guarded submit readiness.
```

Template creation/versioning is related, but it is a separate authoring story.

## 3. Explicit Non-Goals

Order Release Generator is not, for MVP0/MVP1:

```text
- a raw XML editor;
- a production integration runtime;
- an unguarded submit-to-OTM button;
- a credential entry screen;
- a place to paste real customer order data;
- a generic file manager;
- a frontend-owned XML generator;
- a screen that exposes local artifact paths.
```

The backend remains the source of truth for templates, columns, defaults,
validation, XML generation, artifact metadata, downloads, evidence, direct OTM
submit capability, and safety blockers.

## 4. OTM Functional Direction

The OTM schema discovery confirms that this module is aligned with:

```text
Transmission.xsd
Order.xsd
DBXML.xsd
OrderReleaseService.wsdl
CommandService.wsdl
```

Important model guidance:

```text
- Transmission is the broad XML envelope.
- TransmissionBody/GLogXMLElement can carry Release payloads.
- Order.xsd exposes Release and ReleaseLine structures.
- Release has important root-level metadata such as TransactionCode.
- ReleaseLine is repeatable.
- DBXML can become an alternate import/export helper, but should be governed as
  a backend artifact workflow.
```

Future template fields should move toward XSD-backed official Release paths and
schema-pack validation when that shared Catalog/Core capability is ready.

## 5. Current UI Review

Browser review of `/order-release-generator` found a strong backend-backed first
slice but not a final operating model.

Delivered strengths:

```text
- backend-owned template list exists;
- template creation exists;
- template versioning exists;
- field-guided row editor replaced raw JSON;
- batch creation and validation exist;
- invalid row issues are surfaced and block downstream actions;
- XML preview action exists;
- XML artifact generation and guarded download exist;
- direct OTM submit is guarded in MVP0;
- template switching clears stale batch/preview/artifact/submit state;
- raw local artifact paths are not exposed.
```

Current product and UX problems:

1. `/order-release-generator` combines template browsing, template creation,
   template versioning, batch row editing, recent batch recovery, preview,
   artifact generation, submit guard, and selected template detail in one route.
2. Template authoring and template versioning appear above the template list.
   This makes the first screen feel like an admin/configuration page, not a
   generator.
3. The workflow tabs are compact but cramped (`1Templates`, `2Batch`,
   `3Preview`) and do not give enough explanation of lifecycle status.
4. The selected-object side panel is useful, but it is carrying too much detail
   that should be available on a template detail route.
5. Recent batches are visible, but not selectable as first-class objects with a
   dedicated detail route.
6. The batch row editor is technically better than raw JSON, but it will become
   unwieldy with realistic Release/ReleaseLine/ShipUnit-style scenarios.
7. Preview, Artifact, and Submit stages are too thin for their importance.
   Preview needs structured XML summary/provenance; Artifact needs generated
   file metadata; Submit needs an explicit guard/readiness route.
8. There is no clear separation between reusable template design and one-time
   batch execution.
9. There is no route-level story for XML schema validation, official OTM path
   mapping, or schema-pack evidence.
10. The current view proves capability, but a user still has to infer the
    operating model from panels.

Product conclusion:

```text
The current Order Release Generator is a good first functional slice. It should
not be treated as final UX. The next step is a route-level generator workflow
that separates template library, template builder/versioning, batch execution,
XML preview, artifact review, and guarded submit readiness.
```

## 6. Design Decision

Replace the single heavy staged screen with a route-level generator workspace.

The new IA should be:

```text
/order-release-generator
  Generator hub and template library

/order-release-generator/templates/new
  Create template

/order-release-generator/templates/:templateId
  Template detail

/order-release-generator/templates/:templateId/edit
  Edit template draft/header/fields

/order-release-generator/templates/:templateId/version
  Create next template version

/order-release-generator/batches/new
  Create batch from selected template

/order-release-generator/batches/:batchId
  Batch detail and validation

/order-release-generator/batches/:batchId/rows
  Row editor

/order-release-generator/batches/:batchId/preview
  XML preview

/order-release-generator/batches/:batchId/artifacts
  Generated XML/DBXML artifacts

/order-release-generator/batches/:batchId/submit-readiness
  Guarded OTM submit readiness

/order-release-generator/batches/:batchId/history
  Batch activity/evidence
```

Every detail, edit, version, preview, artifact, and submit-readiness route must
have a visible `Back` action.

## 7. Global UX Rules

1. The hub is for finding templates and recent batches, not authoring every
   object.
2. Template authoring/versioning is a separate route family.
3. Batch execution is a separate route family.
4. XML preview is a documented exception where XML may be inspected, but the
   default should be structured summary plus safe preview, not a giant raw XML
   blob.
5. Artifact download must always go through guarded backend endpoints.
6. Direct OTM submit must stay backend-guarded and should never become a
   frontend-only enabled button.
7. Template fields should be backend-owned and eventually reference official
   Release/ReleaseLine paths from schema packs.
8. No real customer order data, endpoint credentials, local paths, CNPJ, CPF, or
   production identifiers should appear in docs, tests, screenshots, or seeds.

## 8. Screen: `/order-release-generator`

### Purpose

Help the user choose whether they are generating a batch from an existing
template or managing templates.

### Backend Loads

```text
GET /api/v1/modules/order-release-generator/templates?filters...
GET /api/v1/modules/order-release-generator/batches?recent=true
GET /api/v1/modules/order-release-generator/summary
GET /api/v1/modules/order-release-generator/filter-options
GET /api/v1/platform/navigation
```

### Main Content

```text
- template library table;
- recent batch table;
- saved views: Active templates, Draft templates, Recently used, Needs schema
  review, Batches with issues;
- primary action: Create batch;
- secondary actions: New template, Template builder, Recent batches.
```

### Searchable Template Header Fields

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
template_code
template_name
client_code
project_code
template_type
macro_object_code
status
version
owner
otm_version
schema_pack_code
release_scenario
transport_mode
tags
description
updated_by
updated_at
```

### Clicks

| Click | Opens |
|---|---|
| `Create batch` | `/order-release-generator/batches/new` |
| template row | `/order-release-generator/templates/:templateId` |
| batch row | `/order-release-generator/batches/:batchId` |
| `New template` | `/order-release-generator/templates/new` |
| saved view/filter | updates backend query and URL state |

### What Must Not Be Here

```text
- template field authoring forms;
- versioning forms;
- full row editor;
- XML preview body;
- submit guard details;
- local artifact paths.
```

## 9. Screen: Create Template

### Route

```text
/order-release-generator/templates/new
```

### Purpose

Create a reusable backend-owned Order Release template.

### Backend Loads

```text
GET /api/v1/modules/order-release-generator/template-create-options
GET /api/v1/catalog/macro-objects?code=ORDER_RELEASE
GET /api/v1/catalog/schema-roots?recommended_module=order_release_generator
GET /api/v1/catalog/schema-roots/{schema_root_id}/paths?root=Release
```

### Fields

```text
template_code
template_name
client_code
project_code
template_type
macro_object_code
otm_version
schema_pack_id
description
tags
required_columns
optional_columns
defaults
field_to_xml_path_mappings
```

### Actions

| Action | Backend execution | Result |
|---|---|---|
| `Create template` | `POST /templates` | navigate to template detail |
| `Validate template` | backend template validation | blockers and warnings displayed |
| `Cancel` | none | back to hub |

## 10. Screen: Template Detail

### Route

```text
/order-release-generator/templates/:templateId
```

### Purpose

Explain what the template generates and whether it is ready for batch creation.

### Backend Loads

```text
GET /api/v1/modules/order-release-generator/templates/{template_id}
GET /api/v1/modules/order-release-generator/templates/{template_id}/versions
GET /api/v1/modules/order-release-generator/templates/{template_id}/available-actions
GET /api/v1/modules/order-release-generator/templates/{template_id}/schema-coverage
```

### Main Content

```text
- template header;
- version summary;
- required and optional fields;
- defaults;
- official XML path coverage;
- sample-safe generated shape summary;
- recent batches from this template;
- available actions.
```

### Clicks

| Click | Opens |
|---|---|
| `Back` | hub with filters preserved |
| `Create batch from template` | `/order-release-generator/batches/new?templateId=...` |
| `Edit template` | `/templates/:templateId/edit` |
| `Create next version` | `/templates/:templateId/version` |
| recent batch row | `/batches/:batchId` |
| XML path row | Catalog/schema path detail if available |

## 11. Screen: Template Versioning

### Route

```text
/order-release-generator/templates/:templateId/version
```

### Purpose

Create a new template version while preserving history.

### Actions

| Action | Backend execution | Result |
|---|---|---|
| `Create version` | `POST /templates/{template_id}/versions` | new version selected |
| `Validate version` | backend validation | blockers shown |
| `Cancel` | none | back to template detail |

Versioning should not live on the generator hub.

## 12. Screen: Create Batch

### Route

```text
/order-release-generator/batches/new
```

### Purpose

Create a batch from a chosen template.

### Backend Loads

```text
GET /api/v1/modules/order-release-generator/templates?filters...
GET /api/v1/modules/order-release-generator/templates/{template_id}
GET /api/v1/modules/order-release-generator/batch-create-options
```

### Main Content

```text
- selected template summary;
- batch metadata;
- row authoring entry point;
- import/upload option if backend supports it later;
- validation summary before create.
```

### Actions

| Action | Backend execution | Result |
|---|---|---|
| `Select template` | local route state/backend selection | row editor fields refresh |
| `Continue to rows` | route navigation | `/batches/new/rows` or inline wizard step |
| `Create batch` | `POST /batches` | navigate to batch detail |
| `Cancel` | none | back to hub/template detail |

## 13. Screen: Batch Detail

### Route

```text
/order-release-generator/batches/:batchId
```

### Purpose

Show batch readiness and next action.

### Backend Loads

```text
GET /api/v1/modules/order-release-generator/batches/{batch_id}
GET /api/v1/modules/order-release-generator/batches/{batch_id}/issues
GET /api/v1/modules/order-release-generator/batches/{batch_id}/available-actions
GET /api/v1/modules/order-release-generator/batches/{batch_id}/artifacts
```

### Main Content

```text
- batch header;
- template used;
- row count and release count;
- validation status and issues;
- lifecycle cards: Rows, Preview, Artifacts, Submit readiness, History;
- next action from backend.
```

### Clicks

| Click | Opens |
|---|---|
| `Back` | hub or template detail, preserving source |
| `Edit rows` | `/batches/:batchId/rows` |
| `Preview XML` | `/batches/:batchId/preview` |
| `Artifacts` | `/batches/:batchId/artifacts` |
| `Submit readiness` | `/batches/:batchId/submit-readiness` |
| issue row | row editor focused on row/field if backend supplies location |

## 14. Screen: Row Editor

### Route

```text
/order-release-generator/batches/:batchId/rows
```

### Purpose

Edit synthetic rows using the template contract.

### UX Pattern

Use a grid/table editor for repeated rows, not a long stack of row cards once
the template has more than a handful of fields.

Required behavior:

```text
- add row;
- duplicate row;
- remove row;
- reset row from template defaults;
- paste/import rows later if backend supports it;
- inline row/field validation;
- sticky actions;
- visible Back action.
```

### Actions

| Action | Backend execution | Result |
|---|---|---|
| `Save rows` | backend row update or recreated batch contract | batch status refreshes |
| `Validate rows` | backend validation | row issues update |
| `Reset from defaults` | backend/default contract | draft reset |
| `Cancel` | none or discard draft | back to batch detail |

## 15. Screen: XML Preview

### Route

```text
/order-release-generator/batches/:batchId/preview
```

### Purpose

Show whether the batch generates the expected OTM XML shape.

### Backend Action

```text
POST /api/v1/modules/order-release-generator/batches/{batch_id}/preview-xml
```

### Main Content

```text
- preview readiness;
- generated root/envelope summary;
- Release count;
- ReleaseLine count;
- TransactionCode handling;
- schema-pack validation status when available;
- safe XML preview section;
- field-to-XML provenance table;
- blockers/warnings.
```

The raw XML preview is allowed as a documented exception, but it must be
client-safe and should not be the only review surface.

## 16. Screen: Artifacts

### Route

```text
/order-release-generator/batches/:batchId/artifacts
```

### Purpose

Generate, review, download, and archive generated XML/DBXML artifacts.

### Backend Actions

```text
POST /api/v1/modules/order-release-generator/batches/{batch_id}/generate-xml-artifact
GET /api/v1/modules/order-release-generator/batches/{batch_id}/artifacts
GET /api/v1/modules/order-release-generator/batches/{batch_id}/artifacts/{artifact_id}/download
```

### Main Content

```text
- generated artifact list;
- artifact type: Transmission XML, DBXML, validation report;
- file name;
- size;
- checksum/hash;
- schema validation result;
- evidence id;
- guarded download;
- Evidence Hub archive action when eligible.
```

## 17. Screen: Submit Readiness

### Route

```text
/order-release-generator/batches/:batchId/submit-readiness
```

### Purpose

Explain whether direct submit to OTM is allowed. In MVP0, this should remain a
guarded readiness surface, not an execution surface.

### Backend Action

```text
POST /api/v1/modules/order-release-generator/batches/{batch_id}/submit-otm
```

### Main Content

```text
- direct submit capability;
- connection configured;
- credential/vault reference configured;
- environment allow-list;
- audit policy;
- artifact hash eligible;
- idempotency/retry policy;
- current blockers;
- next setup steps.
```

If submit becomes enabled in the future, the action must still be backend-owned,
audited, job-based, and explicitly environment-scoped.

## 18. Backend Contract Gaps

The current backend supports the first slice. Route-level UX needs explicit
contracts or aliases for:

```text
GET /templates filtered/paginated list
GET /templates/filter-options
GET /templates/{id}
PATCH /templates/{id}
POST /templates/{id}/copy
POST /templates/{id}/retire
GET /templates/{id}/schema-coverage
GET /templates/{id}/available-actions
GET /batches/{id}
GET /batches/{id}/issues
PATCH /batches/{id}/rows or backend-owned batch row update contract
GET /batches/{id}/available-actions
GET /batches/{id}/history
GET /batches/{id}/submit-readiness
```

Where these already exist under different names, the GUI should consume the
backend contract rather than invent local readiness or XML-generation logic.

## 19. QA Journeys

Required browser/UI QA:

```text
1. search template by code/name/status/version;
2. open template detail and return to hub;
3. create custom template;
4. create next version;
5. create batch from selected template;
6. add, duplicate, remove, reset, and validate rows;
7. create invalid row and verify downstream preview/artifact are blocked;
8. correct invalid row and continue without route reload;
9. preview XML and inspect structure/provenance;
10. generate XML artifact and download through guarded endpoint;
11. inspect submit readiness and confirm MVP0 guard;
12. switch templates while row drafts are dirty;
13. switch batches while preview/artifact/submit state exists;
14. leave and return to hub/template/batch routes;
15. verify no raw real customer data, local path, or credential appears.
```

Visual QA:

```text
- desktop and mobile route fit;
- light/dark/system theme;
- high-volume template list;
- high-volume row editor;
- long OTM GID and XML path wrapping;
- invalid row issue density;
- XML preview readability;
- artifact success state;
- submit blocked state.
```

## 20. Implementation Slices

Recommended implementation order:

```text
1. Hub with template and recent batch library.
2. Template detail route.
3. Create/edit/version template routes.
4. Batch creation route.
5. Batch detail and row editor routes.
6. XML preview route with structured summary/provenance.
7. Artifact route with guarded download/archive.
8. Submit readiness route.
9. Schema-pack coverage links when Catalog Core exposes official Release paths.
10. Browser QA across valid, invalid, out-of-order, and route-return journeys.
```

## 21. Acceptance Criteria

The module can be considered product-ready for this class of generator only
when:

```text
- a user can generate a valid synthetic Order Release XML without hand-writing
  XML;
- template creation/versioning is separated from batch execution;
- batch rows are editable in a usable grid/table pattern;
- invalid rows block preview/artifact with clear row/field reasons;
- XML preview proves envelope, Release, ReleaseLine, and key metadata shape;
- generated artifacts are downloadable only through guarded backend endpoints;
- direct submit remains guarded until connection/credential/audit governance is
  implemented;
- route switching clears stale draft/preview/artifact/submit state;
- docs, tests, Linear, and GitHub point to this spec;
- no real client data is used.
```

## 22. Decision Summary

The current Order Release Generator should remain as functional evidence, not
as final UX direction. The next UX direction is a route-based generator:

```text
Template library -> template detail/builder -> batch detail -> row editor ->
XML preview -> artifacts -> submit readiness.
```

This keeps the module backend-first while making it understandable as an
accelerator for real testing work.

