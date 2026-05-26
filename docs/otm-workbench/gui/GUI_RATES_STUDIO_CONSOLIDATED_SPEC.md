# GUI Rates Studio Consolidated Specification

**Status:** draft for product review
**Date:** 2026-05-26
**Linear:** OTM-165
**Scope:** consolidated Rates Studio objective, current MVP evidence, browser
review findings, GUI information architecture, route map, click-by-click
operating model, and redesign direction.

## 0. Source Documents Consolidated

This document consolidates the Rates Studio direction that was previously split
across focused MVP contracts:

```text
docs/otm-workbench/modules/rates_estado_atual_mvp0.md
docs/otm-workbench/gui/GUI_RATES_SUMMARY_VIEW.md
docs/otm-workbench/gui/GUI_RATES_BATCH_DETAIL_PANEL.md
docs/otm-workbench/gui/GUI_RATES_ACTION_EXECUTION.md
docs/otm-workbench/gui/GUI_RATES_ARTIFACT_DOWNLOAD.md
docs/otm-workbench/gui/GUI_RATES_ARTIFACTS_EVIDENCE.md
docs/otm-workbench/gui/GUI_RATES_MVP_COMPLETION_REVIEW_OTM58.md
docs/otm-workbench/gui/GUI_RATES_VISUAL_QA_OTM78.md
```

Those files remain valid historical evidence. This consolidated spec is the
current navigation point for future Rates Studio UX and implementation work.

## 1. Current UI Review

The current Rates Studio UI is a strong first MVP slice: it proves the backend
contracts, summary metrics, batch selection, backend-owned actions, artifacts,
evidence, and guarded downloads.

The current screen is still not the final operating model. Browser review of
`/rates` showed that one page currently combines:

1. Rates module overview.
2. Recent batch list.
3. Selected batch detail.
4. Batch actions.
5. Table row staging.
6. Open blockers.
7. Artifact list.
8. Evidence list.

This is usable for proving contracts, but it is not yet an intuitive accelerator
for real tariff work. Actions such as `View artifacts` do not open an artifact
screen; they reposition the user inside the same long page. Creating or editing
batch data also happens inside a selected-object panel, which makes the journey
feel like a technical test harness instead of a Rates workspace.

## 2. Product Objective

Rates Studio should help a user prepare, validate, approve, export, and hand
off OTM tariff packages.

The module must support the operational tariff lifecycle:

```text
choose tariff scenario/template
create rate batch
stage or import rate tables
validate OTM table structure and load sequence
review issues
preview CSV package
approve when readiness gates pass
export CSV/ZIP artifacts
review evidence
register/load package into Load Plan
```

Rates Studio does not replace OTM, CSVUTIL, or functional tariff review. It is
the backend-owned preparation and governance workspace before controlled load
execution.

## 3. Design Decision

`/rates` becomes the Rates Studio hub. It should not be the place where every
batch operation happens.

The redesign separates Rates into route-level journeys:

1. **Rates Hub**
   Understand module status, key metrics, open blockers, and recent work.

2. **Batch Library**
   Search, filter, and open rate batches.

3. **Batch Creation**
   Create a batch from a backend-owned tariff scenario/template.

4. **Batch Workspace**
   Inspect one batch and run lifecycle actions from clear sections.

5. **Table Staging**
   Add, upload, edit, or review OTM table rows for one batch.

6. **Validation And Issues**
   Review blockers by table, row, severity, and load-sequence dependency.

7. **CSV Preview And Export**
   Preview generated OTM CSV/ZIP output before export.

8. **Approval**
   Dedicated confirmation screen with readiness gates and audit intent.

9. **Artifacts And Evidence**
   Dedicated review screens for generated artifacts and evidence metadata.

10. **Load Plan Handoff**
    Dedicated handoff screen when a Rates export is ready for cutover planning.

## 4. Core Navigation Map

```text
/rates
  Rates Studio hub

/rates/batches
  Searchable rate batch library

/rates/batches/new
  New rate batch creation wizard

/rates/batches/:batchId
  Rate batch overview/detail

/rates/batches/:batchId/stage
  Table staging workspace

/rates/batches/:batchId/tables/:tableName
  Table row review/edit workspace

/rates/batches/:batchId/issues
  Validation issues and readiness blockers

/rates/batches/:batchId/csv-preview
  Generated CSV preview

/rates/batches/:batchId/export
  Export review and execution

/rates/batches/:batchId/approve
  Approval confirmation and readiness gates

/rates/batches/:batchId/artifacts
  Batch artifact list and guarded downloads

/rates/batches/:batchId/evidence
  Batch evidence list

/rates/batches/:batchId/load-plan
  Load Plan registration and handoff status
```

## 5. Global UX Rules

### 5.1 No Core Work In Selected-Object Side Panels

A selected-object panel may summarize one selected batch, but it must not own
the core lifecycle. Staging, approval, export, artifacts, evidence, and handoff
must open dedicated route-level screens.

### 5.2 One Primary Task Per Screen

Do not stack list, staging form, issue review, artifact download, and evidence
history into one page. Each route should explain one task and one next action.

### 5.3 Back Button Required

Every drill-down route needs a visible `Back` action:

- `Back to Rates`
- `Back to Batches`
- `Back to Batch`
- `Back to Export`
- `Back to Load Plan`

### 5.4 Backend Ownership

The frontend must not infer:

- readiness;
- approval eligibility;
- export eligibility;
- CSV load order;
- table/column validity;
- disabled reasons;
- permissions;
- artifact safety;
- evidence safety.

Those remain backend-owned through Rates, Catalog Core, Evidence Hub, and Load
Plan contracts.

## 6. Screen: `/rates`

### Purpose

Orient the user and show whether tariff work is healthy.

### Layout

- Header: `Rates Studio`
- Primary action: `Create rate batch`
- Secondary action: `Open batch library`
- Metrics:
  - total batches
  - ready for approval
  - ready for export
  - blocked
  - exported
  - recently changed
- Sections:
  - `Recommended next actions`
  - `Recent batches`
  - `Open blockers summary`
  - `Recent exports`

### Clicks

| User click | Opens | Backend load |
|---|---|---|
| `Create rate batch` | `/rates/batches/new` | templates/scenarios, domains, reference options |
| `Open batch library` | `/rates/batches` | searchable batch list metadata |
| Recent batch row | `/rates/batches/:batchId` | batch detail |
| Blocker summary row | `/rates/batches/:batchId/issues` | batch issues |
| Recent export row | `/rates/batches/:batchId/artifacts` | batch artifacts |

### What Must Not Be Here

- row staging forms;
- CSV preview table;
- artifact download list;
- evidence detail list;
- approval confirmation.

## 7. Screen: `/rates/batches`

### Purpose

Find a rate batch by technical and functional qualifiers.

### Batch Header Search Contract

Batch search must be backend-owned. The UI renders searchable fields from
backend search metadata. The MVP baseline should support:

| Field | Purpose | Example |
|---|---|---|
| batch id | technical identifier | `2b86a157...` |
| batch name | user-facing name | `Synthetic LTL/TL stack` |
| scenario | tariff scenario/template | `RATE_GEO_ONLY`, `LTL_TL_RATE_STACK` |
| client | sanitized implementation/client qualifier | `DEMO_CLIENT` |
| domain | OTM domain | `OTM1` |
| macro object | catalog macro-object | `RATE_RECORD` |
| status | lifecycle status | `DRAFT`, `VALIDATED`, `APPROVED`, `EXPORTED` |
| readiness | backend readiness state | `READY`, `BLOCKED` |
| issue severity | highest issue severity | `ERROR`, `WARNING` |
| has export | artifact existence | `true`, `false` |
| created by | user or system actor | `demo-user` |
| updated date | recency filter | `2026-05-26` |
| target OTM version | target baseline | `26A`, `26B` |
| tags | reusable qualifiers | `ltl,tl,accessorial` |
| description | searchable explanation | `Accessorial-only synthetic rate package` |

Every searchable text field supports:

| Operator | Behavior |
|---|---|
| `begins with` | case-insensitive prefix match |
| `contains` | case-insensitive substring match |
| `one of` | comma-separated list; trims spaces around values |
| `not one of` | comma-separated exclusion list; trims spaces around values |

Search behavior rules:

- Multiple filters combine with `AND`.
- Empty filters are ignored.
- Invalid operator/value combinations are blocked before backend call.
- Backend returns normalized filters and pagination metadata.

### Clicks

| User click | Opens | Backend load |
|---|---|---|
| `Apply search` | stays on `/rates/batches` | filtered/paginated batch list |
| `Clear search` | stays on `/rates/batches` | default batch list |
| Batch row | `/rates/batches/:batchId` | batch detail |
| `Create rate batch` | `/rates/batches/new` | templates/scenarios/reference options |
| `Open issues` row action | `/rates/batches/:batchId/issues` | batch issues |
| `Open artifacts` row action | `/rates/batches/:batchId/artifacts` | batch artifacts |

## 8. Screen: `/rates/batches/new`

### Purpose

Create a rate batch deliberately instead of creating a synthetic batch directly
from the hub.

### Layout

Wizard or staged form:

1. `Basics`
2. `Scenario`
3. `Reference Options`
4. `Review`

### Header Fields

- batch name
- client
- domain
- target OTM version
- description
- tags
- scenario/template
- catalog macro-object, backend-controlled and constrained to `RATE_RECORD`

### Actions

| Action | Executes | Result |
|---|---|---|
| `Create batch` | backend batch create | opens `/rates/batches/:batchId` |
| `Save draft` | backend draft create, if supported | opens batch detail or stays with saved state |
| `Cancel` | navigation only | returns to `/rates/batches` |

## 9. Screen: `/rates/batches/:batchId`

### Purpose

Inspect one rate batch and understand the next best action.

### Layout

- `Back to Batches`
- batch title/status/readiness
- next-action panel
- tabs or sections:
  - `Overview`
  - `Tables`
  - `Validation`
  - `CSV`
  - `Approval`
  - `Artifacts`
  - `Evidence`
  - `Load Plan`
- action bar driven by backend `available_actions`.

### Clicks

| Click | Opens |
|---|---|
| `Stage tables` | `/rates/batches/:batchId/stage` |
| table row | `/rates/batches/:batchId/tables/:tableName` |
| `Review issues` | `/rates/batches/:batchId/issues` |
| `Preview CSV` | `/rates/batches/:batchId/csv-preview` |
| `Export CSV` | `/rates/batches/:batchId/export` |
| `Approve` | `/rates/batches/:batchId/approve` |
| `View artifacts` | `/rates/batches/:batchId/artifacts` |
| `View evidence` | `/rates/batches/:batchId/evidence` |
| `Register in Load Plan` | `/rates/batches/:batchId/load-plan` |

## 10. Screen: `/rates/batches/:batchId/stage`

### Purpose

Add or import OTM rate tables for one batch.

### Layout

- `Back to Batch`
- selected scenario and expected table sequence
- table picker
- upload/import area, if supported
- manual row authoring only as an advanced section
- staged table summary

### Actions

| Action | Executes | Result |
|---|---|---|
| `Add table row` | backend table row add | updates staged table summary |
| `Upload workbook/CSV` | backend preview/import | opens import result state |
| `Validate staged data` | backend validation | opens `/rates/batches/:batchId/issues` if issues exist |
| `Continue to CSV Preview` | navigation guarded by readiness | `/rates/batches/:batchId/csv-preview` |

### UX Requirement

Manual row authoring cannot be the main visible story for production tariff
work. It may remain as an advanced/test utility, but the primary path should be
template/workbook/import driven.

## 11. Screen: `/rates/batches/:batchId/tables/:tableName`

### Purpose

Review one OTM table inside a rate batch.

### Layout

- `Back to Batch`
- table name, role, load-order position, row count, issue count
- compact row grid
- row detail drawer or route-level row detail if editing becomes complex
- Data Dictionary metadata summary

### Actions

| Action | Executes | Result |
|---|---|---|
| `Add row` | backend row create | row appears in grid |
| `Edit row` | backend row patch, if supported | row validation refreshed |
| `Delete row` | backend row delete, if allowed | impact/validation refreshed |
| `Validate table` | backend validation scoped to table | issue summary updated |

## 12. Screen: `/rates/batches/:batchId/issues`

### Purpose

Make blockers actionable.

### Layout

- `Back to Batch`
- readiness summary
- issue groups:
  - table/column issues
  - load sequence issues
  - missing data
  - export blockers
  - approval blockers
- filters for severity, table, code, and status

### Actions

| Action | Executes | Result |
|---|---|---|
| `Run validation` | backend validation | refreshed issue groups |
| issue row click | navigation to table/row context if available | user can fix source |
| `Export issue report` | backend artifact/export, if supported | artifact link |

## 13. Screen: `/rates/batches/:batchId/csv-preview`

### Purpose

Preview generated OTM CSV output before export.

### Layout

- `Back to Batch`
- package summary
- file list by table
- selected CSV preview
- alter-session/date notice when applicable
- Data Dictionary/load-order summary

### Actions

| Action | Executes | Result |
|---|---|---|
| `Generate preview` | backend CSV preview | preview files refreshed |
| `Export CSV package` | navigation to export review | `/rates/batches/:batchId/export` |
| `Download preview report` | guarded artifact/download if available | download |

## 14. Screen: `/rates/batches/:batchId/export`

### Purpose

Run final CSV/ZIP export from a clear review screen.

### Layout

- `Back to Batch`
- readiness gates
- package contents
- manifest summary
- known blockers/warnings
- export confirmation

### Actions

| Action | Executes | Result |
|---|---|---|
| `Run export` | backend CSV/ZIP export | opens artifacts screen or shows artifact link |
| `Review CSV preview` | navigation | `/rates/batches/:batchId/csv-preview` |
| `Cancel` | navigation | `/rates/batches/:batchId` |

## 15. Screen: `/rates/batches/:batchId/approve`

### Purpose

Approve a rate batch with explicit readiness, audit intent, and confirmation.

### Layout

- `Back to Batch`
- readiness gates
- open blockers/warnings
- approval consequences
- confirmation input or checkbox

### Actions

| Action | Executes | Result |
|---|---|---|
| `Approve batch` | backend approval action | returns to batch detail with approved status |
| `Run readiness` | backend readiness check | refreshed gates |
| `Cancel` | navigation | returns to batch detail |

## 16. Screen: `/rates/batches/:batchId/artifacts`

### Purpose

Review and download generated artifacts without exposing local paths.

### Layout

- `Back to Batch`
- artifact list
- artifact type/content type/size/sensitivity
- generation source
- hash/audit metadata, if exposed client-safe

### Actions

| Action | Executes | Result |
|---|---|---|
| `Download` | guarded backend artifact download | browser download |
| artifact row | artifact metadata detail | route or inline detail |
| `Open evidence` | navigation | `/rates/batches/:batchId/evidence` |

## 17. Screen: `/rates/batches/:batchId/evidence`

### Purpose

Review evidence generated by validation, approval, export, and handoff.

### Layout

- `Back to Batch`
- evidence list grouped by type
- status, sensitivity, artifact-link indicator
- client-safe metadata only

### Actions

| Action | Executes | Result |
|---|---|---|
| evidence row | open evidence detail if available | route/detail |
| `Open artifacts` | navigation | `/rates/batches/:batchId/artifacts` |
| `Archive in Evidence Hub` | backend Evidence Hub archive, if supported | archive result |

## 18. Screen: `/rates/batches/:batchId/load-plan`

### Purpose

Register an approved/exported Rates package into Load Plan without making
cutover decisions inside Rates.

### Layout

- `Back to Batch`
- latest export summary
- handoff eligibility
- Load Plan package registration state
- links to generated Load Plan package/checklist when available

### Actions

| Action | Executes | Result |
|---|---|---|
| `Register package` | backend Load Plan intake from Rates export | package link/status |
| `Open Load Plan package` | navigation | `/load-plan/...` route when available |
| `Refresh eligibility` | backend readiness/eligibility query | updated gates |

## 19. Backend Contract Alignment

The redesign should reuse existing backend contracts:

- `GET /api/v1/modules/rates/summary`
- `GET /api/v1/modules/rates/templates`
- `POST /api/v1/modules/rates/batches`
- `GET /api/v1/modules/rates/batches`
- `GET /api/v1/modules/rates/batches/{batch_id}`
- `POST /api/v1/modules/rates/batches/{batch_id}/tables`
- `POST /api/v1/modules/rates/batches/{batch_id}/validate`
- `GET /api/v1/modules/rates/batches/{batch_id}/issues`
- `POST /api/v1/modules/rates/batches/{batch_id}/csv-preview`
- `POST /api/v1/modules/rates/batches/{batch_id}/export-csv`
- `GET /api/v1/modules/rates/batches/{batch_id}/readiness`
- `POST /api/v1/modules/rates/batches/{batch_id}/approve`
- `GET /api/v1/modules/rates/batches/{batch_id}/artifacts`
- `GET /api/v1/modules/rates/batches/{batch_id}/evidence`
- `GET /api/v1/modules/rates/batches/{batch_id}/exports/latest`
- `GET /api/v1/modules/rates/batches/{batch_id}/artifacts/{artifact_id}/download`
- dictionary/reference endpoints.

Potential backend/API improvements:

1. searchable/paginated batch library endpoint with normalized filters;
2. batch creation metadata endpoint for scenarios, domains, options, and
   default header values;
3. route-optimized batch workspace endpoint grouped by lifecycle area;
4. table detail endpoint with row grid pagination and Data Dictionary metadata;
5. explicit export review/readiness endpoint before final ZIP generation;
6. Load Plan handoff eligibility endpoint scoped to a Rates export.

## 20. QA Journeys

Functional browser QA must cover:

1. create batch from scenario and return to batch detail;
2. search batch by scenario/status/domain using operators;
3. open batch detail, leave, return, and preserve backend-owned state;
4. stage table row or import data, validate, and review issues;
5. blocked batch cannot approve/export;
6. approved/exportable batch can preview CSV and export package;
7. artifact download uses guarded backend download;
8. evidence list shows client-safe metadata only;
9. Load Plan handoff is available only after export eligibility;
10. switching batches clears draft row state, preview state, export feedback, and
    stale action feedback.

## 21. Implementation Slices

### Slice 1: Routing And Hub Cleanup

- Keep `/rates` as hub.
- Move batch lifecycle work out of selected-object panel.
- Add route links for batch library and batch detail.

### Slice 2: Batch Library

- Build `/rates/batches`.
- Add backend-owned searchable header fields and operators.
- Add row actions that navigate to detail/issues/artifacts.

### Slice 3: Batch Creation

- Build `/rates/batches/new`.
- Create batch through a deliberate form/wizard.
- Remove direct one-click synthetic batch creation from the hub.

### Slice 4: Batch Workspace

- Build `/rates/batches/:batchId`.
- Add next-action panel and route links for stage/issues/csv/export/approve.
- Keep backend `available_actions` as source of truth.

### Slice 5: Dedicated Lifecycle Screens

- Build stage, issues, CSV preview, export, approval, artifacts, evidence, and
  Load Plan handoff routes.
- Keep each route one-task focused.

### Slice 6: QA And Documentation

- Update React and browser QA for route leave/return and out-of-order actions.
- Update Linear issues and module docs.
- Keep synthetic data only.

## 22. Acceptance Criteria

The redesign is accepted when:

1. `/rates` explains the module and recent state without hosting the whole
   lifecycle.
2. Batch rows open route-level detail pages with `Back`.
3. Create batch opens a deliberate screen instead of executing a hidden default.
4. Search supports backend-owned batch header fields and operators.
5. Staging, validation/issues, CSV preview, export, approval, artifacts,
   evidence, and Load Plan handoff each have a clear route or section-level
   task boundary.
6. Artifact/evidence actions open dedicated review screens instead of scrolling
   the same long page.
7. The frontend does not infer readiness, approval, export, permission, table,
   load-order, artifact, or evidence rules.
8. Functional QA covers happy, negative, out-of-order, and route recovery paths.
9. No real client data appears in docs, UI fixtures, screenshots, or tests.

## 23. Explicit Non-Goals

- Do not connect directly to real OTM from Rates in this redesign.
- Do not execute CSVUTIL real from Rates.
- Do not replace functional tariff review.
- Do not expose CSV row payloads on the hub page.
- Do not expose local artifact file paths.
- Do not make Rates own Load Plan or Cutover decisions.
