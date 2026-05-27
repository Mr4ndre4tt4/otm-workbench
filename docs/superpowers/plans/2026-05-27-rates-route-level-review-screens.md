# Rates Route-Level Review Screens Plan

## Goal

Complete route-level Rates review screens for CSV preview, export, and
approval.

## Tasks

- [x] Define task contract and scope guardrails.
- [x] Add failing functional assertions for direct review routes.
- [x] Extend Rates route parser for `csv-preview`, `export`, and `approve`.
- [x] Render CSV preview route.
- [x] Render export review route.
- [x] Render approval review route.
- [x] Run functional validation and build.
- [x] Capture browser QA evidence.
- [x] Update validation and handoff docs.

## Validation Commands

```powershell
npm test -- src/app/AppFunctionalRates.test.tsx
npm run build
git diff --check
```

## Result

- `/rates/batches/:batchId/csv-preview` renders `Rate CSV preview`.
- `/rates/batches/:batchId/export` renders `Rate export review`.
- `/rates/batches/:batchId/approve` renders `Rate approval review`.
- Export and approval remain explicit confirmation flows.

## Evidence

```text
npm test -- src/app/AppFunctionalRates.test.tsx
AppFunctionalRates.test.tsx: 3 passed

npm run build
frontend build: passed

Browser QA:
var/qa/rates-route-level-review-screens.png
```
