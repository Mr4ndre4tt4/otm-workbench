# GUI Load Plan View

**Status:** implemented
**Branch:** `codex/gui-load-plan-view`

## Objective

Add the first backend-backed Load Plan screen using the shared GUI foundation.

Load Plan now renders package summary, package list, selected package load
sequence, and the first cutover checklist workflow slice from backend contracts
instead of the generic module placeholder.

## Backend Contracts

The GUI consumes:

```text
GET /api/v1/modules/load-plan/summary
GET /api/v1/modules/load-plan/packages
GET /api/v1/modules/load-plan/packages/{package_id}
POST /api/v1/modules/load-plan/cutover-checklists/from-package/{package_id}
PATCH /api/v1/modules/load-plan/cutover-checklists/items/{item_id}
POST /api/v1/modules/load-plan/cutover-checklists/{checklist_id}/readiness
POST /api/v1/modules/load-plan/csvutil/build/from-cutover-checklist/{checklist_id}
POST /api/v1/modules/load-plan/zip-analysis
POST /api/v1/modules/load-plan/review-queue/from-zip-analysis/{analysis_id}
GET /api/v1/modules/load-plan/review-queue?package_id={package_id}
POST /api/v1/modules/load-plan/review-queue/{item_id}/decide
POST /api/v1/modules/load-plan/sequence/snapshots
POST /api/v1/modules/load-plan/cutover-readiness/generate
POST /api/v1/modules/load-plan/cutover-readiness/{readiness_id}/export
POST /api/v1/modules/load-plan/cutover-checklists/{checklist_id}/export-package
POST /api/v1/modules/load-plan/cutover-checklists/{checklist_id}/go-no-go
GET /api/v1/modules/load-plan/cutover-handoff/eligibility?package_id={package_id}
```

## GUI Behavior

Primary pattern:

```text
review queue + staged workflow
```

First delivered story:

```text
select package -> create checklist -> mark item CSVUTIL-ready with evidence ->
generate checklist readiness -> build CSVUTIL CTL/CL artifacts from checklist ->
download generated CSVUTIL artifact -> run ZIP analysis -> generate review queue ->
decide review item when present -> generate sequence snapshot and inspect blockers/next actions ->
generate package readiness -> export readiness ZIP -> export cutover package ->
download exported artifact through Evidence Hub -> inspect handoff eligibility ->
archive readiness export through Evidence Hub -> record Go/No-Go decision ->
commit cutover handoff when backend eligibility allows -> leave route ->
return with backend-owned package state visible
```

The screen uses shared components:

```text
- MetricGrid for registered package, source, catalog macro, and visible row counters;
- ModuleObjectList for selectable Load Plan packages in the package stage;
- SelectedObjectPanel for selected package metadata;
- DetailList for the selected package load sequence, readiness counts,
  CSVUTIL artifact ids, ZIP findings, sequence blockers, export artifact ids,
  Go/No-Go decision, and handoff facts;
- ArtifactList for downloadable CSVUTIL and exported Load Plan artifacts;
- OperationalPanel, FeedbackMessage, Button, and BlockerPanel for checklist,
  readiness, CSVUTIL, ZIP review, exports, and handoff stages.
```

The first selected package defaults to the first backend item. Selecting
another package updates the detail query through backend-owned ids.

## Safety

```text
- No client-specific sample data in tests or docs.
- No frontend-only package registration decisions.
- No frontend-only CSVUTIL, cutover readiness, or handoff actions.
- CSVUTIL uses the backend build-from-checklist endpoint and backend-owned
  artifact/evidence/manifest ids.
- ZIP review uses backend-owned analysis, review queue, decision, evidence, and
  Data Dictionary findings.
- Sequence snapshots and Go/No-Go decisions use backend-owned endpoints and
  returned evidence/blocker state.
- Cutover handoff commit uses backend-owned eligibility and commit endpoints;
  the button remains disabled while eligibility has blockers.
- Readiness export archive convenience calls the Evidence Hub archive endpoint
  with load-plan readiness-export filters; Evidence Hub still owns archive
  creation, evidence, audit, and event records.
- Exports use backend-owned readiness export and cutover package artifacts; the
  frontend only displays returned artifact/evidence/manifest ids.
- No local artifact path rendering.
- Artifact downloads use the guarded Evidence Hub artifact download endpoint.
- Package status, catalog macro, evidence references, artifact references, and load sequence come from backend contracts.
```

The GUI does not bypass Evidence Hub archive or readiness gates. If eligibility
is blocked, the Handoff stage renders backend blockers and leaves commit
disabled.

## Validation

Commands executed:

```text
cd frontend
npm run test -- AppFunctionalLoadPlan.test.tsx
npm run qa:functional:load-plan:browser
```
