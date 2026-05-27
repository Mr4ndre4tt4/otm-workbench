# Task Contract: Rates Batch Library Search UX

**Status:** active
**Date:** 2026-05-27

## Objective

Continue Rates Studio completion by replacing reliance on recent batches with a
visible batch library/search surface.

## Original User Request

The user asked to continue after Rates approval/export review gating. The
recorded next step is the batch-library/search slice.

## Interpreted Scope

- Use the existing `GET /api/v1/modules/rates/batches` endpoint.
- Render a `Rate batch library` panel in the current Rates workspace.
- Add search, status, and domain filters over the backend-returned library.
- Keep current selected-batch workspace and action behavior intact.
- Keep this as a transition slice before full route-level `/rates/batches`
  implementation.

## Out Of Scope

- New backend search operators.
- Pagination controls.
- Full `/rates/batches` route-family implementation.
- Data Dictionary validation changes.
- Real tariff data.

## Allowed Files Or Areas

- `frontend/src/platform/types/rates.ts`
- `frontend/src/platform/hooks/rates.ts`
- `frontend/src/modules/rates/RatesSummaryView.tsx`
- `frontend/src/app/AppFunctionalRates.test.tsx`
- `frontend/src/ui/layouts.css`
- `docs/agent/TASK_CONTRACT_RATES_BATCH_LIBRARY_SEARCH_UX.md`
- `docs/superpowers/plans/2026-05-27-rates-batch-library-search-ux.md`
- `docs/agent/VALIDATION_REPORT.md`
- `docs/agent/HANDOFF.md`

## Protected Files Or Areas

- Backend Rates endpoints unless a failing test proves a contract gap.
- Approval/export backend logic.
- Load Plan handoff behavior.

## Acceptance Criteria

- Rates loads the backend batch library endpoint.
- Users can filter the library by free text, status, and domain.
- Filtered library rows can select the active batch.
- Existing Rates functional journeys remain green.
- Browser QA captures the filtered library state.

## Validation Plan

```powershell
npm test -- src/app/AppFunctionalRates.test.tsx
npm run build
git diff --check
```

## Risks

- Local filters are a transition step; the spec eventually calls for
  backend-owned search metadata/operators.
- Avoid implying pagination or full route ownership before the route family is
  implemented.

## Decision

Proceed with a focused frontend batch-library/search slice using the existing
backend list endpoint.
