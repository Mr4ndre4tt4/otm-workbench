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
GET /api/v1/modules/load-plan/cutover-handoff/eligibility?package_id={package_id}
```

## GUI Behavior

Primary pattern:

```text
review queue + staged workflow
```

First delivered story:

```text
select package -> create checklist -> update item evidence/status ->
generate checklist readiness -> inspect handoff eligibility -> leave route ->
return with backend-owned package state visible
```

The screen uses shared components:

```text
- MetricGrid for registered package, source, catalog macro, and visible row counters;
- ModuleObjectList for selectable Load Plan packages in the package stage;
- SelectedObjectPanel for selected package metadata;
- DetailList for the selected package load sequence, readiness counts, and
  handoff facts;
- OperationalPanel, FeedbackMessage, Button, and BlockerPanel for checklist,
  readiness, and handoff stages.
```

The first selected package defaults to the first backend item. Selecting
another package updates the detail query through backend-owned ids.

## Safety

```text
- No client-specific sample data in tests or docs.
- No frontend-only package registration decisions.
- No frontend-only CSVUTIL, cutover readiness, or handoff actions.
- No local artifact path rendering.
- Package status, catalog macro, evidence references, artifact references, and load sequence come from backend contracts.
```

Out of current scope:

```text
- CSVUTIL build UI;
- ZIP analysis UI;
- full review queue decision UI;
- package registration from Rates/Master Data inside the Load Plan route;
- go/no-go commit;
- handoff commit;
- artifact download from Load Plan.
```

Those actions stay follow-up slices and must continue through backend-owned
available actions or explicit guarded endpoints.

## Validation

Commands executed:

```text
cd frontend
npm run test -- AppFunctionalLoadPlan.test.tsx
npm run qa:functional:load-plan:browser
```
