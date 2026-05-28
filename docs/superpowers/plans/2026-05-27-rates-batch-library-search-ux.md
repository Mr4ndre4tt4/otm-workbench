# Rates Batch Library Search UX Plan

## Goal

Give Rates Studio a searchable batch library backed by the existing batch list
endpoint.

## Tasks

- [x] Define task contract and scope guardrails.
- [x] Add failing functional assertions for batch library filters.
- [x] Add frontend hook/type for `GET /rates/batches`.
- [x] Render batch library filters and filtered rows.
- [x] Preserve existing selected-batch workspace behavior.
- [x] Run Rates functional validation and build.
- [x] Capture browser QA evidence.
- [x] Update validation and handoff docs.

## Validation Commands

```powershell
npm test -- src/app/AppFunctionalRates.test.tsx
npm run build
git diff --check
```

## Result

- Added a searchable `Rate batch library` panel to `/rates`.
- Filters cover free-text search, status, and domain.
- Selecting a filtered row updates the existing selected-batch workspace and
  lifecycle links.
- Browser QA caught that the backend list contract is compact and does not
  include `tables`; the frontend type now reflects that and the UI falls back
  to `0 table(s)` when the list item is compact.

## Evidence

```text
npm test -- src/app/AppFunctionalRates.test.tsx
AppFunctionalRates.test.tsx: 2 passed

npm run build
frontend build: passed

Browser QA:
var/qa/rates-batch-library-search.png
```
