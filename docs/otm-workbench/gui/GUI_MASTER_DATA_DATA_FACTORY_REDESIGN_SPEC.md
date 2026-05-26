# Data Factory UX Redesign Specification

**Status:** draft for product review
**Date:** 2026-05-26
**Scope:** Master Data / Data Factory GUI information architecture and click-by-click operating model.

## 1. Problem Statement

The current Data Factory screen overloads one page with three different jobs:

1. Operational Data Factory work: use a published template to download, fill, upload, validate, and export OTM CSV/ZIP files.
2. Template authoring work: create or edit templates, table mappings, labels, fixed values, versions, and publish state.
3. Data quality tooling: Lat/Lon validation for Location data.

The result is a confusing single workflow with steps such as `Author`, `Map`,
and `Quality` beside operational steps such as `Workbook`, `Upload`, and
`Output`. Those steps do not belong to one user journey.

This redesign separates the module by user intent, keeps each screen focused,
and moves complex objects to detail pages instead of side panels.

## 2. Design Decision

`/master-data` becomes a hub with three entry points:

1. **Data Factory**
   Use existing published templates to prepare OTM load files.

2. **Template Builder**
   Create, edit, map, validate, version, and publish reusable templates.

3. **Quality Tools**
   Run independent data quality utilities, starting with Lat/Lon Validator.

No screen should combine these three responsibilities.

## 3. Core Navigation Map

```text
/master-data
  Master Data hub

/master-data/factory
  Published templates and recent operational batches

/master-data/factory/templates/:templateCode
  Published template detail and workbook actions

/master-data/factory/batches/:batchId
  Batch execution workspace

/master-data/template-builder
  Template drafts, published templates, versions, and create action

/master-data/template-builder/new
  New template authoring wizard

/master-data/template-builder/:templateCode
  Template builder detail, authoring, mapping, validation, publish/version actions

/master-data/template-builder/:templateCode/edit
  Dedicated template edit screen with Back action

/master-data/template-builder/:templateCode/copy
  Dedicated template copy screen with Back action and new-header review

/master-data/template-builder/:templateCode/delete
  Dedicated delete/retire confirmation screen with Back action

/master-data/quality
  Quality tools hub

/master-data/quality/lat-lon
  Lat/Lon validator workspace

/master-data/quality/lat-lon/batches/:batchId
  Lat/Lon validation result detail
```

## 4. Global UX Rules

### 4.1 No Heavy Side Panels

Do not use a persistent `Selected object` side panel for templates, batches,
template definitions, authoring fields, validation results, or quality results.

Allowed side-panel content:

- short read-only summary
- small next-action hint
- temporary filter help

Not allowed:

- full object detail
- action list
- long metadata
- nested tables
- authoring controls

Complex object click opens a route-level detail screen with a visible `Back`
button.

### 4.2 One Primary Task Per Screen

Every screen must answer:

- What object am I working on?
- What is the next meaningful action?
- What is blocked, and why?
- Where do I go back?

If a screen needs more than one primary action family, split it.

### 4.3 Workflows Belong To Objects, Not Module Landing Pages

A staged workflow is valid only after the user has selected an object that
actually moves through states.

Valid:

- batch detail workflow: `Upload/Created -> Validate -> Output -> CSV -> Export -> Load Plan`
- template builder workflow: `Define -> Map -> Validate -> Publish`
- lat/lon batch workflow: `Upload/Preview -> Validate -> Review -> Export`

Invalid:

- one module-level workflow mixing template list, authoring, upload, map,
  output, and quality tools.

## 5. Screen: `/master-data`

### Purpose

Let the user choose the correct Master Data job without seeing operational
details too early.

### Layout

- Page title: `Master Data`
- Subtitle: `Prepare OTM master data loads, manage templates, and run quality checks.`
- Three large action cards in a single row or responsive grid:
  - `Data Factory`
  - `Template Builder`
  - `Quality Tools`
- Optional recent activity strip below the cards.

### Clicks

| User click | Opens | Backend load | Notes |
|---|---|---|---|
| `Data Factory` card | `/master-data/factory` | template list summary, recent batches summary | Main operational path. |
| `Template Builder` card | `/master-data/template-builder` | templates/drafts/versions summary | Advanced/configuration path. |
| `Quality Tools` card | `/master-data/quality` | available quality tools summary | Independent utilities. |
| Recent batch row | `/master-data/factory/batches/:batchId` or quality batch detail | batch detail | Type determines destination. |

### Primary Actions

- `Open Data Factory`
- `Open Template Builder`
- `Open Quality Tools`

### Empty State

If no templates or batches exist, cards remain visible. Do not show a blank
module.

## 6. Screen: `/master-data/factory`

### Purpose

Operational template consumption. This is for users who have a published
template and need to generate OTM load files.

### What The Screen Shows

- Header: `Data Factory`
- Short purpose text: `Use published templates to create validated OTM CSV/ZIP load packages.`
- Search/filter row:
  - search by template code/name
  - macro object filter
  - status filter, default `Published`
- Main content:
  - `Published templates` list/table
  - `Recent batches` list/table below or in a separate tab

No `Author`, `Map`, or `Quality` steps appear here.

### Template Row

Each row shows:

- template code
- name
- macro object
- version
- target table count
- field count
- last exported batch, if any
- status

### Clicks

| User click | Opens | Backend load | Notes |
|---|---|---|---|
| Template row | `/master-data/factory/templates/:templateCode` | template definition, actions, recent batches for template | Route-level detail. |
| `Download workbook` row action | stays on page or opens download confirmation state | `POST /templates/{code}/build-workbook`, artifact download metadata | Must show progress and success. |
| `Upload completed workbook` row action | `/master-data/factory/templates/:templateCode?intent=upload` | template detail, upload contract | Prefer opening detail with upload panel focused. |
| Recent batch row | `/master-data/factory/batches/:batchId` | batch detail, actions, artifacts | Batch detail owns execution. |
| `Create from editor` row action | `/master-data/factory/templates/:templateCode?intent=editor` | workbook editor contract | Optional operational data entry path. |
| `Template Builder` link | `/master-data/template-builder/:templateCode` | builder detail | Only visible to authorized users. |

### Primary Action

If no template is selected:

- `Choose a template`

If the user has permission and wants config:

- Secondary: `Manage templates`

### What Each Action Executes

| Action | Executes | Success state | Failure state |
|---|---|---|---|
| Download workbook | create workbook artifact for template and start guarded download | toast/inline status: workbook generated, artifact id, download link | show backend error, do not fake download |
| Upload completed workbook | navigates to template detail upload section | upload form focused | if template unavailable, show blocked detail page |
| Create from editor | navigates to template detail editor section | editor contract loaded | missing editor contract shown as unavailable |
| Open batch | navigates to batch detail | batch status and actions loaded | not found page with back to Data Factory |

## 7. Screen: `/master-data/factory/templates/:templateCode`

### Purpose

Explain one published template and let the user start operational work from it.

### Layout

- Top bar:
  - `Back to Data Factory`
  - template code/name/status/version
  - primary action button based on backend next action
- Summary band:
  - macro object
  - target tables
  - field count
  - latest batch
  - latest export
- Tabs or sections:
  1. `Overview`
  2. `Workbook`
  3. `Upload`
  4. `Editor`
  5. `Batches`

### Clicks

| User click | Opens/changes | Backend load | Notes |
|---|---|---|---|
| `Back to Data Factory` | `/master-data/factory` | list reload or cached list | Must preserve filters when possible. |
| `Workbook` tab | same route, tab state | workbook build status/artifacts | No full page reload needed. |
| `Upload` tab | same route, tab state | upload requirements | Shows drag/drop and expected format. |
| `Editor` tab | same route, tab state | workbook editor contract | For small/manual batches. |
| `Batches` tab | same route, tab state | batch list filtered by template | Opens rows to batch detail. |
| Batch row | `/master-data/factory/batches/:batchId` | batch detail | Execution moves to batch route. |
| `Open in Template Builder` | `/master-data/template-builder/:templateCode` | template builder detail | Advanced users only. |

### Actions

| Action | Executes | Then opens |
|---|---|---|
| `Download workbook` | `POST /templates/{code}/build-workbook`; guarded artifact download | stays on template detail; shows generated artifact and download status |
| `Upload workbook` | multipart upload to create batch | `/master-data/factory/batches/:batchId` |
| `Create batch from editor` | validate editor rows, create batch | `/master-data/factory/batches/:batchId` |
| `Validate template definition` | backend template definition validation | stays on template detail; shows validation result |
| `Register latest export in Load Plan` | if latest exported batch exists, register package | `/load-plan/packages/:packageId` or stays with success link |

### Do Not Show Here

- field-by-field authoring grid
- table/field checkbox wall
- publish/version controls inline
- lat/lon validator

## 8. Screen: `/master-data/factory/batches/:batchId`

### Purpose

Operate one concrete master data batch from input to OTM CSV/ZIP package.

### Layout

- Top bar:
  - `Back to template`
  - batch name/id/status
  - template link
- Workflow strip:
  1. `Input`
  2. `Validate`
  3. `Output`
  4. `CSV Package`
  5. `Load Plan`
- Main panel displays only the active step.
- Right side may show a compact status summary, but not full object detail.

### Workflow Step: Input

Shows:

- upload metadata or editor-created rows
- source file name
- row count
- template code/version
- import issues, if any

Actions:

| Action | Executes | Result |
|---|---|---|
| `Replace upload` | new upload against same template | creates new batch or new batch version; confirm if replacing is destructive |
| `Download original input` | guarded artifact download if available | download |
| `Go to validation` | changes active step | no backend mutation |

### Workflow Step: Validate

Shows:

- relationship validation state
- blockers grouped by table/field/rule
- warnings
- pass/fail summary

Actions:

| Action | Executes | Result |
|---|---|---|
| `Validate relationships` | `POST /batches/{id}/validate-relationships` | validation result persisted |
| `Map records` | `POST /batches/{id}/map` | records mapped if validation allows |
| `Open issue details` | same screen detail drawer/modal or issue section | do not navigate unless issue detail is complex |

### Workflow Step: Output

Shows:

- mapped OTM records
- table grouping
- row count by table
- output preview

Actions:

| Action | Executes | Result |
|---|---|---|
| `Build output` | `POST /batches/{id}/build-output` | output records generated |
| `Preview output records` | load output records endpoint | read-only preview |
| `Go to CSV package` | changes active step | no backend mutation |

### Workflow Step: CSV Package

Shows:

- CSV preview per OTM table
- CSVUTIL format readiness
- generated artifact metadata
- manifest summary

Actions:

| Action | Executes | Result |
|---|---|---|
| `Build CSV preview` | `POST /batches/{id}/build-csv` | CSV preview persisted |
| `Export CSV/ZIP package` | `POST /batches/{id}/export-csv-package` | ZIP artifact, manifest, evidence |
| `Download ZIP` | guarded artifact download | download |

### Workflow Step: Load Plan

Shows:

- export package readiness
- registration status
- existing package link if already registered

Actions:

| Action | Executes | Result |
|---|---|---|
| `Register in Load Plan` | Load Plan package intake from batch/export | opens package link or shows success |
| `Open Load Plan package` | navigates to Load Plan package detail | `/load-plan/...` |

### Batch Detail State Rules

- If no validation exists, output and CSV actions are disabled with reason.
- If validation has blockers, export is disabled with reason.
- If export exists, download and Load Plan registration are available.
- If user navigates away and returns, all persisted states reload from backend.
- Changing template never mutates this batch. User must go back and create another batch.

## 9. Screen: `/master-data/template-builder`

### Purpose

Advanced template administration. This screen is not part of the operational
Data Factory load flow.

### Layout

- Header: `Template Builder`
- Subtitle: `Create, map, validate, version, and publish reusable master data templates.`
- Primary action: `Create template`
- Search and filter panel above the list
- List with tabs:
  - `Published`
  - `Drafts`
  - `Needs validation`
  - `Archived`

### Template Header Search Contract

Template search must be backend-owned. The UI renders searchable fields from
the template header/search metadata returned by the backend, but the MVP0
baseline should support these fields:

| Field | Purpose | Example |
|---|---|---|
| template code | technical identifier | `LOCATIONS_STANDARD` |
| template name | user-facing name | `Locations Standard` |
| client | implementation/client qualifier; never real client data in seed/demo docs | `DEMO_CLIENT` |
| type | template family or business type | `MASTER_DATA`, `RATE`, `CUTOVER` |
| macro object | OTM object group | `LOCATION`, `ITEM`, `RATE` |
| status | lifecycle state | `DRAFT`, `PUBLISHED`, `ARCHIVED` |
| version | template version | `1`, `2` |
| scenario pack | source scenario/package | `LOCATION_BASELINE` |
| owner team | functional owner | `TRANSPORTATION`, `MASTER_DATA` |
| tags | reusable qualifiers | `dock,capacity,address` |
| source basis | origin of definition | `DATA_DICTIONARY`, `OFFICIAL_DOC`, `CUSTOM` |
| target OTM version | intended OTM version | `26A` |
| description | searchable business explanation | `Location template with address and dock fields` |

Every searchable field supports the same operator set:

| Operator | Behavior |
|---|---|
| `begins with` | case-insensitive prefix match |
| `contains` | case-insensitive substring match |
| `one of` | comma-separated list; trims spaces around values |
| `not one of` | comma-separated exclusion list; trims spaces around values |

Search behavior rules:

- Multiple filters combine with `AND`.
- `one of` and `not one of` values are entered as comma-separated values in one
  field, for example `LOCATION,ITEM,RATE`.
- Empty values are ignored, not sent as broken filters.
- Invalid operator/value combinations show a local validation message before
  calling the backend.
- Backend returns the normalized filters applied so the UI can show the active
  search state.
- Saved searches may come later, but must be backend-owned if implemented.

### Template List Row Actions

Row actions are secondary and never execute destructive or complex authoring
work inline.

| Row action | Opens | Backend load |
|---|---|---|
| `View` or row click | `/master-data/template-builder/:templateCode` | full template detail |
| `Edit` | `/master-data/template-builder/:templateCode/edit` | editable template detail, locks/permissions |
| `Copy` | `/master-data/template-builder/:templateCode/copy` | source template detail and proposed new header |
| `Delete` or `Retire` | `/master-data/template-builder/:templateCode/delete` | impact summary, usage count, permissions |
| `Open in Data Factory` | `/master-data/factory/templates/:templateCode` | published operational detail |

### Clicks

| User click | Opens | Backend load |
|---|---|---|
| `Create template` | `/master-data/template-builder/new` | scenario packs, macro objects, table metadata |
| Template row | `/master-data/template-builder/:templateCode` | full template draft/detail |
| Search `Apply` | stays on `/master-data/template-builder` | filtered template list and normalized filters |
| Search `Clear` | stays on `/master-data/template-builder` | unfiltered default list |
| `Edit` row action | `/master-data/template-builder/:templateCode/edit` | editable template detail |
| `Copy` row action | `/master-data/template-builder/:templateCode/copy` | source detail and proposed new header |
| `Delete` row action | `/master-data/template-builder/:templateCode/delete` | deletion/retirement impact summary |
| `Open in Data Factory` | `/master-data/factory/templates/:templateCode` | published operational detail |

## 10. Screen: `/master-data/template-builder/new`

### Purpose

Create a reusable template without overloading the operational Data Factory.

### Layout

Wizard or staged page:

1. `Basics`
2. `Tables`
3. `Fields`
4. `Mapping`
5. `Review`

The authoring actions are visible in a sticky top or footer action bar.

### Step: Basics

Fields:

- template code
- template name
- macro object
- description
- source scenario pack, optional

Actions:

| Action | Executes |
|---|---|
| `Continue` | frontend validation only; no draft save required unless backend needs draft early |
| `Save draft` | creates draft template |
| `Cancel` | returns to Template Builder list |

### Step: Tables

Shows table candidates as a compact table, not large cards.

Columns:

- include checkbox
- table name
- role
- required
- relationship role
- data category

Actions:

| Action | Executes |
|---|---|
| `Add selected tables` | updates local draft or backend draft |
| `Continue` | moves to Fields |
| `Save draft` | persists selected tables |

### Step: Fields

Shows selected fields in a dense table, not card grid.

Columns:

- include
- OTM table
- OTM column
- data type
- required
- friendly label
- source type
- fixed value, if applicable

Actions:

| Action | Executes |
|---|---|
| `Save field mappings` | persists draft field mapping |
| `Bulk set source type` | updates selected fields |
| `Continue` | moves to Mapping |

### Step: Mapping

Purpose:

- define 1 input field to N OTM fields
- define fixed values
- define relationship rules
- define derived values only if backend supports them

Actions:

| Action | Executes |
|---|---|
| `Add mapping rule` | opens a focused mapping-rule form or inline row |
| `Validate draft` | backend template definition validation |
| `Continue to Review` | moves to Review if blockers allow |

### Step: Review

Shows:

- template summary
- tables
- fields
- fixed values
- relationship rules
- validation blockers

Actions:

| Action | Executes |
|---|---|
| `Validate definition` | backend validation |
| `Publish template` | backend publish, if validation passes |
| `Back to edit` | returns to prior step |

## 11. Screen: `/master-data/template-builder/:templateCode`

### Purpose

Edit or inspect one template. This replaces the current confusing side-panel +
hidden authoring controls.

### Layout

- `Back to Template Builder`
- template title/status/version
- action bar:
  - `Edit`
  - `Copy`
  - `Delete` or `Retire`
  - `Create next version`
  - `Open in Data Factory`
- tabs:
  - `Overview`
  - `Tables`
  - `Fields`
  - `Mapping`
  - `Versions`
  - `Validation`

### Click Rules

| Click | Opens |
|---|---|
| table row | table detail section within same route |
| field row | field mapping editor panel within same route |
| version row | version detail read-only state |
| `Edit` | `/master-data/template-builder/:templateCode/edit` |
| `Copy` | `/master-data/template-builder/:templateCode/copy` |
| `Delete` or `Retire` | `/master-data/template-builder/:templateCode/delete` |
| `Open in Data Factory` | `/master-data/factory/templates/:templateCode` |

### Actions

| Action | Executes | Result |
|---|---|---|
| `Validate definition` | backend validation | validation tab/result |
| `Publish` | backend publish | status published, action disabled if already published |
| `Create next version` | backend version create | route updates to new version/draft |

### Visual Requirements

- No field card wall.
- Tables and fields use dense rows with stable columns.
- Long OTM column names truncate with tooltip or expand-on-row detail.
- Primary actions are always visible at top or sticky bottom.

## 12. Screen: `/master-data/template-builder/:templateCode/edit`

### Purpose

Edit one template in a focused route. This screen is the only place where
existing template header, table, field, mapping, and validation settings are
changed.

### Layout

- `Back to Template Detail`
- template identity/status/version summary
- warning banner if editing a published template requires creating a draft or
  next version
- tabs:
  - `Header`
  - `Tables`
  - `Fields`
  - `Mapping`
  - `Review`
- sticky action bar:
  - `Save draft`
  - `Validate definition`
  - `Publish`
  - `Discard changes`

### Header Fields

The editable header should include at least:

- template code, read-only after creation unless copying
- template name
- client
- type
- macro object
- status, backend-controlled
- version, backend-controlled
- scenario pack
- owner team
- tags
- source basis
- target OTM version
- description

### Actions

| Action | Executes | Result |
|---|---|---|
| `Save draft` | backend template draft patch/update | stays on edit screen, shows saved state |
| `Validate definition` | backend validation | opens `Review` tab with blockers/warnings |
| `Publish` | backend publish/version promotion | navigates to detail route if successful |
| `Discard changes` | backend/local draft discard depending on state | returns to template detail |
| `Back to Template Detail` | navigation only; warn if unsaved changes | `/master-data/template-builder/:templateCode` |

## 13. Screen: `/master-data/template-builder/:templateCode/copy`

### Purpose

Create a new draft template from an existing template without mutating the
source.

### Layout

- `Back to Template Detail`
- source template summary, read-only
- new template header form
- copy options:
  - copy tables
  - copy fields
  - copy fixed values
  - copy relationship rules
  - copy validation rules
  - copy tags
- preview of resulting draft scope

### Actions

| Action | Executes | Result |
|---|---|---|
| `Create copy` | backend clone/create draft from source with new header | opens new template edit route |
| `Reset header` | frontend reset to backend proposed defaults | stays on copy screen |
| `Cancel` | navigation only | returns to source template detail |

## 14. Screen: `/master-data/template-builder/:templateCode/delete`

### Purpose

Confirm deletion, archive, or retirement in a focused screen with impact
visibility. Published templates that have historical batches should normally be
retired/archived instead of hard-deleted.

### Layout

- `Back to Template Detail`
- template summary
- backend impact summary:
  - published status
  - active batches
  - historical batches
  - dependent saved searches or references, if any
  - whether hard delete is allowed
- confirmation input for destructive actions

### Actions

| Action | Executes | Result |
|---|---|---|
| `Archive` or `Retire` | backend lifecycle transition | returns to Template Builder list with status filter |
| `Delete draft` | backend hard delete only when allowed | returns to Template Builder list |
| `Cancel` | navigation only | returns to template detail |

## 15. Screen: `/master-data/quality`

### Purpose

Separate quality utilities from Data Factory operations.

### Layout

- Header: `Quality Tools`
- Tool cards:
  - `Lat/Lon Validator`

### Clicks

| User click | Opens | Backend load |
|---|---|---|
| `Lat/Lon Validator` | `/master-data/quality/lat-lon` | recent coordinate batches |

## 16. Screen: `/master-data/quality/lat-lon`

### Purpose

Validate Location coordinates independently from template download/upload/export.

### Layout

- Header: `Lat/Lon Validator`
- Primary action: `Upload locations file`
- Sections:
  - upload/preview
  - recent validation batches
  - provider/settings summary, if configured

### Clicks And Actions

| User click/action | Executes | Then opens |
|---|---|---|
| `Upload locations file` | create coordinate quality preview/batch | `/master-data/quality/lat-lon/batches/:batchId` |
| Recent batch row | load batch detail | `/master-data/quality/lat-lon/batches/:batchId` |
| `Export correction package` | export quality review artifact | stays on batch detail with artifact link |

## 17. Screen: `/master-data/quality/lat-lon/batches/:batchId`

### Purpose

Inspect coordinate validation results and export review/correction artifacts.

### Layout

- `Back to Quality Tools`
- batch status and counts
- map/diagnostic placeholder only if supported
- results table grouped by issue type
- export action area

### Actions

| Action | Executes | Result |
|---|---|---|
| `Run validation` | coordinate quality validation endpoint | persisted results |
| `Export correction package` | export endpoint | artifact/evidence |
| `Download package` | guarded artifact download | download |

## 18. Backend Contract Alignment

The redesign should reuse existing backend contracts where possible:

- templates list/detail/actions
- build workbook
- workbook editor contract
- upload/create batch
- validate relationships
- map records
- build output
- build CSV
- export CSV package
- guarded artifact download
- Load Plan package intake
- coordinate quality validate/batches/results/export

Potential backend/API improvements:

1. template detail endpoint optimized for operational Data Factory detail
2. batch detail endpoint with grouped available actions by workflow stage
3. route-safe latest artifact/download metadata per batch
4. template builder endpoints separated from operational template consumption
5. template header search endpoint with backend-owned searchable fields,
   operators, normalized filters, and pagination/sort metadata
6. template copy endpoint that clones a source template into a new draft using
   a reviewed header and selected copy options
7. template delete/retire endpoint that returns impact constraints and only
   allows hard delete when safe
8. quality tools index endpoint, if more quality utilities are added

## 19. Implementation Slices

### Slice 1: Routing And Hub

- Create `/master-data` hub.
- Add route destinations for Data Factory, Template Builder, and Quality Tools.
- Keep old route behavior behind redirects or route-compatible components.

### Slice 2: Operational Data Factory List And Template Detail

- Build `/master-data/factory`.
- Build `/master-data/factory/templates/:templateCode`.
- Remove heavy selected-object side panel from operational flow.
- Move workbook/upload/editor/batches into template detail sections.

### Slice 3: Batch Detail Workflow

- Build `/master-data/factory/batches/:batchId`.
- Move validate/map/output/csv/export/load-plan actions into batch detail.
- Add state recovery tests for leaving and returning.

### Slice 4: Template Builder Separation

- Build `/master-data/template-builder`.
- Move `Author` and mapping controls out of Data Factory.
- Add backend-owned template header search with operators: `begins with`,
  `contains`, `one of`, and `not one of`.
- Add dedicated routes for `Edit`, `Copy`, and `Delete/Retire`, each with a
  visible Back action and no inline destructive execution from the list.
- Replace field card wall with dense table and row editor.

### Slice 5: Quality Tools Separation

- Build `/master-data/quality`.
- Move Lat/Lon Validator into `/master-data/quality/lat-lon`.
- Remove `Quality` from Data Factory workflow.

### Slice 6: QA And Cleanup

- Update functional QA scripts for the new route map.
- Add negative/out-of-order tests:
  - user opens batch before validation
  - user tries export before output
  - user switches templates mid-upload
  - user returns from Load Plan
  - user opens Template Builder from Data Factory and comes back
- Update docs and Linear issues.

## 20. Acceptance Criteria

The redesign is accepted when:

1. A new user can explain the three entry points after seeing `/master-data`.
2. The operational Data Factory path does not show authoring or quality controls.
3. Clicking a template opens a route-level detail page with a `Back` button.
4. Clicking a batch opens a route-level batch execution page.
5. Template authoring is reachable but separated as `Template Builder`.
6. Lat/Lon validation is reachable but separated as `Quality Tools`.
7. Template search supports backend-owned searchable header fields with
   `begins with`, `contains`, `one of`, and `not one of` operators.
8. Template edit, copy, and delete/retire actions open dedicated screens with
   Back actions and clear impact/state handling.
9. No screen relies on a heavy selected-object side panel for core actions.
10. Primary actions are visible without scrolling to the bottom of a long form.
11. Long table/field names do not overlap.
12. All critical actions execute backend-owned contracts and show backend errors.
13. Functional QA covers the happy path and realistic human out-of-order paths.

## 21. Explicit Non-Goals

- Do not redesign the whole Workbench shell.
- Do not remove backend capabilities.
- Do not merge Template Builder and Data Factory back into one staged workflow.
- Do not make Lat/Lon a step in Data Factory export.
- Do not expose real client data in tests or documentation.

## 22. Implementation Log

### 2026-05-26 Slice 1

Delivered the first routing and hub slice:

- `/master-data` now opens a focused Master Data hub with Data Factory,
  Template Builder, and Quality Tools entry points.
- `/master-data/factory` keeps the existing operational workflow while hiding
  authoring and quality stages from the Data Factory stage strip.
- `/master-data/template-builder` opens the authoring-focused route family and
  keeps `Templates` available only as builder context for recovering existing
  definitions.
- `/master-data/quality` opens the Lat/Lon quality route family without making
  it a Data Factory export step.
- React and browser QA scripts were updated to enter the correct route family
  instead of assuming the sidebar link opens the operational workflow directly.

Evidence generated:

- `frontend/src/app/App.test.tsx`
- `frontend/src/app/AppFunctionalMasterData.test.tsx`
- `frontend/src/app/AppFunctionalCoordinateQuality.test.tsx`
- `frontend/scripts/functional-master-data-browser.mjs`
- `frontend/scripts/functional-coordinate-quality-browser.mjs`
- `output/gui-qa/master-data/01-master-data-hub.png`
- `output/gui-qa/master-data/02-template-builder-entry.png`
- `output/gui-qa/master-data/03-data-factory-entry.png`

### 2026-05-26 Slice 2A

Delivered the first route-level operational template detail slice:

- Template selection from `/master-data/factory` now opens
  `/master-data/factory/templates/:templateCode`.
- Template detail has a visible `Back to Data Factory` action.
- Template detail shows an operational summary, sheets, and fields in the main
  route content instead of relying on the persistent selected-object side
  panel.
- Data Factory route state now separates factory landing and factory detail
  stages so returning from a template detail lands back on the template list.
- The existing operational workflow remains available on the template detail
  route while the next slice moves batch execution into first-class batch
  routes.

Evidence generated:

- `frontend/src/app/App.test.tsx`
- `frontend/src/app/AppFunctionalMasterData.test.tsx`
- `frontend/scripts/functional-master-data-browser.mjs`
- `output/gui-qa/master-data/04-template-detail-regions-basic.png`
