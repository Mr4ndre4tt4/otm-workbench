# Rates Route-Level Batch Screens Plan

## Goal

Turn Rates lifecycle links for batch overview, staging, and issues into real
route-level screens with direct URL recovery.

## Tasks

- [x] Define task contract and scope guardrails.
- [x] Add failing functional assertions for direct batch routes.
- [x] Add frontend issue-list hook/type.
- [x] Parse Rates route mode from URL.
- [x] Render route-level batch overview.
- [x] Render route-level staging workflow.
- [x] Render route-level issue review.
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

- `/rates/batches/:batchId` renders `Rate batch overview`.
- `/rates/batches/:batchId/stage` renders `Stage rate batch tables` and reuses
  the existing backend staging action.
- `/rates/batches/:batchId/issues` renders `Rate batch issues` backed by the
  backend issue-list contract.
- Each route has `Back to Rates` and adjacent lifecycle links.

## Evidence

```text
npm test -- src/app/AppFunctionalRates.test.tsx
AppFunctionalRates.test.tsx: 3 passed

npm run build
frontend build: passed

Browser QA:
var/qa/rates-route-level-batch-issues.png
```
