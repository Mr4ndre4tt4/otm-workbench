# GUI Load Plan / Cutover Consolidated Specification

**Status:** draft for product review
**Date:** 2026-05-26
**Linear:** OTM-166
**Scope:** consolidated Load Plan and Cutover objective, current MVP evidence,
browser review findings, GUI information architecture, route map,
click-by-click operating model, and redesign direction.

## 0. Source Documents Consolidated

This document consolidates the Load Plan / Cutover direction that is currently
spread across roadmap, GUI, QA, and CSVUTIL reference documents:

```text
docs/otm-workbench/gui/GUI_LOAD_PLAN_VIEW.md
docs/otm-workbench/gui/GUI_MODULE_EXPERIENCE_ROADMAP.md
docs/otm-workbench/gui/GUI_FUNCTIONAL_QA_JOURNEYS.md
docs/otm-workbench/gui/GUI_GENERAL_SOLUTION_QA_2026_05_25.md
docs/otm-workbench/reference/csvutil_reference_archive_notes_2026-05-25.md
docs/otm-workbench/roadmap/backlog_pos_rates.md
```

Those files remain valid supporting evidence. This consolidated spec is the
current navigation point for future Load Plan / Cutover UX and implementation
work.

## 1. Product Objective

Load Plan / Cutover should govern the operational path from generated load
packages to cutover readiness and handoff.

The module exists to answer:

```text
What packages are in scope?
What order should they load in?
What checklist/readiness evidence exists?
What CSVUTIL package can be generated?
What ZIP/package findings require review?
What blockers prevent cutover?
What artifacts/evidence prove the decision?
Can this package be handed off?
```

Load Plan does not create the business data itself. It consumes packages from
Rates, Master Data/Data Factory, and future generators, then governs sequence,
CSVUTIL, readiness, review, evidence, Go/No-Go, and handoff.

## 2. Current UI Review

The current `/load-plan` screen is a strong first backend-backed MVP slice. It
proves package intake, package selection, selected package details, checklist
creation, readiness, CSVUTIL build, ZIP review, sequence snapshot, exports,
Go/No-Go, handoff blockers, guarded downloads, and package-switch cleanup.

Browser review found that it is not yet the final operating model:

1. `/load-plan` is doing too much as one route.
2. The initial package list can dominate the screen; the tested page had more
   than 4,000px of height because package rows repeat in one long list.
3. Workflow stages (`Packages`, `Checklist`, `Readiness`, `CSVUTIL`, `ZIP
   review`, `Sequence`, `Exports`, `Handoff`) change internal state but do not
   open route-level task screens.
4. Critical operational actions such as `Generate readiness`, `Build CSVUTIL`,
   `Run ZIP analysis`, `Export cutover package`, `Archive readiness export`,
   `Decide Go/No-Go`, and `Commit cutover handoff` are all siblings in one
   staged route instead of having route-level context.
5. The selected-object side panel summarizes package metadata well, but it
   should not own the operating model.
6. The next-action panel is useful, but some next actions can point to a future
   prerequisite while the active stage is later in the workflow, making the user
   wonder why they are on `Handoff` while the action says `Create checklist`.

The current screen works as contract evidence. To become genuinely clear for a
user, Load Plan needs a route-level story: hub, package library, package detail,
and dedicated workspaces for checklist, readiness, CSVUTIL, ZIP review,
sequence, exports, Go/No-Go, and handoff.

## 3. Design Decision

`/load-plan` becomes the module hub. It should show status, health, recommended
next actions, and recent packages, but it should not host the entire cutover
journey.

The redesign separates Load Plan into route-level journeys:

1. **Load Plan Hub**
   Understand overall package health, blockers, and recent handoff state.

2. **Package Library**
   Search/filter package intake records from Rates, Master Data, and future
   sources.

3. **Package Detail**
   Inspect one package, load sequence, status, source, readiness summary, and
   next best action.

4. **Cutover Checklist**
   Create or maintain checklist items and evidence for one package.

5. **Readiness**
   Generate and review checklist/package/cutover readiness.

6. **CSVUTIL Builder**
   Generate and review CSVUTIL CTL/CL/manifest artifacts.

7. **ZIP Review**
   Run ZIP analysis, create review queue, and decide findings.

8. **Sequence**
   Generate and inspect sequence snapshots and blockers.

9. **Exports**
   Generate readiness ZIP and cutover package export artifacts.

10. **Go/No-Go**
    Record a governed decision with backend readiness and evidence context.

11. **Handoff**
    Review eligibility and commit cutover handoff only when backend allows it.

## 4. Core Navigation Map

```text
/load-plan
  Load Plan hub

/load-plan/packages
  Searchable package library

/load-plan/packages/:packageId
  Package detail and next-action summary

/load-plan/packages/:packageId/checklist
  Cutover checklist workspace

/load-plan/packages/:packageId/readiness
  Checklist/package/cutover readiness workspace

/load-plan/packages/:packageId/csvutil
  CSVUTIL build and artifact review workspace

/load-plan/packages/:packageId/zip-review
  ZIP analysis and review queue workspace

/load-plan/packages/:packageId/sequence
  Sequence snapshot and blocker review workspace

/load-plan/packages/:packageId/exports
  Readiness ZIP and cutover package export workspace

/load-plan/packages/:packageId/go-no-go
  Go/No-Go decision workspace

/load-plan/packages/:packageId/handoff
  Handoff eligibility and commit workspace

/load-plan/artifacts/:artifactId
  Guarded artifact detail/download metadata, if Evidence Hub route is not used
```

## 5. Global UX Rules

### 5.1 Do Not Put The Entire Cutover Journey On One Page

The current staged workflow is useful as a mental model, but each operational
stage must have a route-level task screen when it contains important actions,
evidence, blockers, or artifacts.

### 5.2 Package Is The Primary Object

Most routes are scoped to `packageId`. The package is the anchor for checklist,
readiness, CSVUTIL, ZIP analysis, sequence, exports, Go/No-Go, and handoff.

### 5.3 Back Button Required

Every drill-down route needs a visible `Back` action:

- `Back to Load Plan`
- `Back to Packages`
- `Back to Package`
- `Back to Readiness`
- `Back to Exports`

### 5.4 Backend Ownership

The frontend must not infer:

- package eligibility;
- cutover readiness;
- checklist readiness;
- CSVUTIL command correctness;
- ZIP finding severity;
- review queue decisions;
- sequence blockers;
- Go/No-Go eligibility;
- handoff eligibility;
- artifact safety;
- evidence safety.

Those remain backend-owned through Load Plan, Catalog Core, Evidence Hub, and
source-module contracts.

### 5.5 Cutover Is A Governed Flow, Not A Dashboard Decoration

Metrics are useful, but the user must always know the next operational step and
why the backend says it is available, blocked, or complete.

## 6. Screen: `/load-plan`

### Purpose

Orient the user and show package/cutover health without exposing the whole
workflow on the landing page.

### Layout

- Header: `Load Plan`
- Primary action: `Open package library`
- Metrics:
  - total packages
  - sources
  - catalog macros
  - packages with blockers
  - ready for handoff
  - recently exported
- Sections:
  - `Recommended next actions`
  - `Recent packages`
  - `Open handoff blockers`
  - `Recent exports`

### Clicks

| User click | Opens | Backend load |
|---|---|---|
| `Open package library` | `/load-plan/packages` | searchable package metadata |
| Recent package row | `/load-plan/packages/:packageId` | package detail |
| Blocker row | `/load-plan/packages/:packageId/handoff` or readiness route | blocker detail |
| Recent export row | `/load-plan/packages/:packageId/exports` | export artifacts |

### What Must Not Be Here

- full package list with many repeated rows;
- checklist item editing;
- CSVUTIL build actions;
- ZIP review queue decisions;
- Go/No-Go form;
- handoff commit button.

## 7. Screen: `/load-plan/packages`

### Purpose

Find packages by source, macro-object, status, readiness, and handoff state.

### Package Header Search Contract

Package search must be backend-owned. The UI renders searchable fields from
backend metadata. The MVP baseline should support:

| Field | Purpose | Example |
|---|---|---|
| package id | technical identifier | `pkg_...` |
| package name | user-facing name | `rates_csv_zip` |
| source module | producing module | `rates`, `master_data` |
| source entity | producing entity type | `rate_batch`, `master_data_batch` |
| source entity id | source object id | `batch_...` |
| client | sanitized implementation/client qualifier | `DEMO_CLIENT` |
| domain | OTM domain | `OTM1` |
| catalog macro | macro-object | `RATE_RECORD`, `REGION`, `LOCATION` |
| status | lifecycle status | `REGISTERED`, `READY`, `HANDED_OFF` |
| readiness | backend readiness state | `READY`, `BLOCKED` |
| handoff eligibility | backend eligibility | `ELIGIBLE`, `INELIGIBLE` |
| has checklist | checklist exists | `true`, `false` |
| has csvutil | CSVUTIL artifact exists | `true`, `false` |
| has export | export artifact exists | `true`, `false` |
| blocker code | blocker or issue code | `CUTOVER_READINESS_MISSING` |
| target OTM version | target baseline | `26A`, `26B` |
| tags | reusable qualifiers | `mock,crp,cutover` |
| description | searchable explanation | `Rates package for synthetic CRP` |

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
| `Apply search` | stays on `/load-plan/packages` | filtered package list |
| `Clear search` | stays on `/load-plan/packages` | default package list |
| Package row | `/load-plan/packages/:packageId` | package detail |
| `Open checklist` row action | `/load-plan/packages/:packageId/checklist` | checklist detail |
| `Open handoff` row action | `/load-plan/packages/:packageId/handoff` | eligibility facts |

## 8. Screen: `/load-plan/packages/:packageId`

### Purpose

Inspect one load package and decide the next best operational step.

### Layout

- `Back to Packages`
- package title/status/source/macro-object
- next-action panel
- load sequence summary
- readiness summary
- artifact/evidence summary
- links to stage routes:
  - `Checklist`
  - `Readiness`
  - `CSVUTIL`
  - `ZIP review`
  - `Sequence`
  - `Exports`
  - `Go/No-Go`
  - `Handoff`

### Clicks

| Click | Opens |
|---|---|
| `Create/Open checklist` | `/load-plan/packages/:packageId/checklist` |
| `Review readiness` | `/load-plan/packages/:packageId/readiness` |
| `Build CSVUTIL` | `/load-plan/packages/:packageId/csvutil` |
| `Run ZIP review` | `/load-plan/packages/:packageId/zip-review` |
| `Review sequence` | `/load-plan/packages/:packageId/sequence` |
| `Open exports` | `/load-plan/packages/:packageId/exports` |
| `Decide Go/No-Go` | `/load-plan/packages/:packageId/go-no-go` |
| `Review handoff` | `/load-plan/packages/:packageId/handoff` |

## 9. Screen: `/load-plan/packages/:packageId/checklist`

### Purpose

Create and maintain the cutover checklist for one package.

### Actions

| Action | Executes | Result |
|---|---|---|
| `Create checklist` | backend checklist-from-package endpoint | checklist items appear |
| `Update item status/evidence` | backend item patch | item refreshes |
| `Reset evidence draft` | frontend route-session reset only | draft returns to baseline |
| `Generate readiness` | backend readiness generation | opens readiness route or updates readiness summary |

## 10. Screen: `/load-plan/packages/:packageId/readiness`

### Purpose

Generate and inspect checklist/package/cutover readiness.

### Actions

| Action | Executes | Result |
|---|---|---|
| `Generate checklist readiness` | backend checklist readiness endpoint | readiness result and blockers |
| `Generate package readiness` | backend cutover readiness generation | readiness artifact/result |
| blocker row click | opens source checklist/item/detail when possible | user can resolve source |
| `Open exports` | navigation | `/load-plan/packages/:packageId/exports` |

## 11. Screen: `/load-plan/packages/:packageId/csvutil`

### Purpose

Build and review CSVUTIL artifacts without executing CSVUTIL real.

### Actions

| Action | Executes | Result |
|---|---|---|
| `Build CSVUTIL` | backend build-from-checklist endpoint | CTL/CL/manifest artifact ids |
| `Download CSVUTIL artifact` | guarded Evidence Hub download | browser download |
| `Open ZIP review` | navigation | `/load-plan/packages/:packageId/zip-review` |

## 12. Screen: `/load-plan/packages/:packageId/zip-review`

### Purpose

Analyze exported ZIP/package structure and govern review decisions.

### Actions

| Action | Executes | Result |
|---|---|---|
| `Run ZIP analysis` | backend ZIP analysis endpoint | findings grouped by severity/source |
| `Generate review queue` | backend review queue generation | queue rows |
| `Decide review item` | backend review queue decision | row state and evidence refresh |

## 13. Screen: `/load-plan/packages/:packageId/sequence`

### Purpose

Generate and inspect sequence snapshot and sequence blockers.

### Actions

| Action | Executes | Result |
|---|---|---|
| `Generate sequence snapshot` | backend sequence snapshot endpoint | ordered steps/blockers |
| sequence row click | opens package/table context when available | contextual detail |

## 14. Screen: `/load-plan/packages/:packageId/exports`

### Purpose

Generate and review readiness ZIP and cutover package exports.

### Actions

| Action | Executes | Result |
|---|---|---|
| `Export readiness` | backend readiness export endpoint | readiness artifact |
| `Export cutover package` | backend checklist package export | cutover package artifact |
| `Archive readiness export` | Evidence Hub archive endpoint | archive id/status |
| `Download artifact` | guarded Evidence Hub download | browser download |

## 15. Screen: `/load-plan/packages/:packageId/go-no-go`

### Purpose

Record a Go/No-Go decision with explicit backend readiness and evidence context.

### Actions

| Action | Executes | Result |
|---|---|---|
| `Record Go` | backend Go/No-Go endpoint | decision and evidence refresh |
| `Record No-Go` | backend Go/No-Go endpoint | blockers/reason captured |
| `Cancel` | navigation only | returns to package detail |

## 16. Screen: `/load-plan/packages/:packageId/handoff`

### Purpose

Review handoff eligibility and commit cutover handoff only when backend gates
allow it.

### Actions

| Action | Executes | Result |
|---|---|---|
| `Refresh eligibility` | backend eligibility query | facts/blockers refresh |
| `Commit cutover handoff` | backend handoff commit endpoint | handoff event/evidence |
| blocker row click | opens readiness/checklist/export route when possible | user can fix prerequisite |

## 17. Backend Contract Alignment

The redesign should reuse existing backend contracts:

- `GET /api/v1/modules/load-plan/summary`
- `GET /api/v1/modules/load-plan/packages`
- `GET /api/v1/modules/load-plan/packages/{package_id}`
- `POST /api/v1/modules/load-plan/cutover-checklists/from-package/{package_id}`
- `PATCH /api/v1/modules/load-plan/cutover-checklists/items/{item_id}`
- `POST /api/v1/modules/load-plan/cutover-checklists/{checklist_id}/readiness`
- `POST /api/v1/modules/load-plan/csvutil/build/from-cutover-checklist/{checklist_id}`
- `POST /api/v1/modules/load-plan/zip-analysis`
- `POST /api/v1/modules/load-plan/review-queue/from-zip-analysis/{analysis_id}`
- `GET /api/v1/modules/load-plan/review-queue?package_id={package_id}`
- `POST /api/v1/modules/load-plan/review-queue/{item_id}/decide`
- `POST /api/v1/modules/load-plan/sequence/snapshots`
- `POST /api/v1/modules/load-plan/cutover-readiness/generate`
- `POST /api/v1/modules/load-plan/cutover-readiness/{readiness_id}/export`
- `POST /api/v1/modules/load-plan/cutover-checklists/{checklist_id}/export-package`
- `POST /api/v1/modules/load-plan/cutover-checklists/{checklist_id}/go-no-go`
- `GET /api/v1/modules/load-plan/cutover-handoff/eligibility?package_id={package_id}`

Potential backend/API improvements:

1. searchable/paginated package library endpoint with normalized filters;
2. route-optimized package workspace endpoint grouped by lifecycle area;
3. dedicated stage summary endpoint per package for checklist/readiness/csvutil/
   zip-review/sequence/exports/handoff;
4. direct blocker-to-route metadata so the UI can send users to the right
   prerequisite screen;
5. artifact/evidence summary endpoint scoped to package and stage.

## 18. QA Journeys

Functional browser QA must cover:

1. open hub, open package library, search/filter, open package detail;
2. create checklist, leave route, return, and see backend-owned checklist state;
3. update checklist item/evidence and verify draft reset behavior;
4. generate readiness and inspect blockers;
5. build CSVUTIL and download guarded artifact;
6. run ZIP analysis, generate review queue, decide review item;
7. generate sequence snapshot and inspect blockers;
8. export readiness and cutover package artifacts;
9. archive readiness export through Evidence Hub;
10. record Go/No-Go only when backend allows it;
11. commit handoff only when eligibility is true;
12. switch packages and verify stale checklist/readiness/csvutil/zip/export/
    handoff state is cleared.

## 19. Implementation Slices

### Slice 1: Hub And Package Library

- Keep `/load-plan` as hub.
- Build `/load-plan/packages`.
- Add backend-owned package search metadata, operators, pagination, and row
  actions.

### Slice 2: Package Detail

- Build `/load-plan/packages/:packageId`.
- Move selected-object side panel content into route-level detail.
- Add next-action panel and stage links.

### Slice 3: Checklist And Readiness

- Build checklist and readiness routes.
- Keep backend readiness/blocker state as source of truth.

### Slice 4: CSVUTIL, ZIP Review, Sequence

- Build route-level CSVUTIL, ZIP review, and sequence screens.
- Keep artifacts and review decisions backend-owned.

### Slice 5: Exports, Go/No-Go, Handoff

- Build route-level export, decision, and handoff screens.
- Keep Evidence Hub archive and handoff commit backend-owned.

### Slice 6: QA And Documentation

- Update React/browser QA for route leave/return and package switching.
- Update Linear and module docs.
- Keep synthetic data only.

## 20. Acceptance Criteria

The redesign is accepted when:

1. `/load-plan` explains module health without hosting the full cutover journey.
2. Package rows open route-level detail pages with `Back`.
3. Checklist, readiness, CSVUTIL, ZIP review, sequence, exports, Go/No-Go, and
   handoff each have a clear route-level task boundary.
4. Package search supports backend-owned header fields and operators.
5. Critical actions show backend blockers/eligibility, not frontend-inferred
   state.
6. Artifact downloads and Evidence Hub archive actions remain guarded.
7. Package switching clears stale route-session outputs.
8. Functional QA covers happy, negative, out-of-order, and route recovery paths.
9. No real client data appears in docs, UI fixtures, screenshots, or tests.

## 21. Explicit Non-Goals

- Do not execute real CSVUTIL in MVP0.
- Do not execute real OTM load from Load Plan.
- Do not replace human cutover decision-making.
- Do not make the frontend decide cutover readiness or handoff eligibility.
- Do not expose local artifact paths.
- Do not make Load Plan own source module data authoring.
