# Task Contract: Rates Route-Level Batch Screens

## Objective

Add route-level Rates screens for batch overview, table staging, and issue
review so lifecycle links from `/rates` lead to deliberate destinations.

## Original User Request

`siga com o próximo passo.`

## Interpreted Scope

- Implement `/rates/batches/:batchId`.
- Implement `/rates/batches/:batchId/stage`.
- Implement `/rates/batches/:batchId/issues`.
- Keep all screens inside existing Rates UI patterns and backend-owned
  contracts.
- Provide visible return paths to `/rates` and adjacent Rates lifecycle routes.

## Out Of Scope

- New backend endpoints.
- Server-side pagination/search for batch library.
- CSV preview/export/approval route screens.
- Load Plan handoff implementation.

## Allowed Files Or Areas

- `frontend/src/modules/rates/RatesSummaryView.tsx`
- `frontend/src/platform/hooks/rates.ts`
- `frontend/src/platform/types/rates.ts`
- `frontend/src/app/AppFunctionalRates.test.tsx`
- `frontend/src/ui/layouts.css`
- `docs/agent/*`
- `docs/superpowers/plans/*`

## Protected Files Or Areas

- Backend Rates behavior unless a frontend contract mismatch blocks the slice.
- Unrelated modules and dirty worktree changes.

## Acceptance Criteria

- Direct URL `/rates/batches/:batchId` renders route-level batch overview.
- Direct URL `/rates/batches/:batchId/stage` renders stage-row workflow and
  preserves existing add-table behavior.
- Direct URL `/rates/batches/:batchId/issues` renders issue review from
  `GET /api/v1/modules/rates/batches/:batchId/issues`.
- Each screen has a visible `Back to Rates` route.
- Existing Rates functional journeys continue to pass.

## Validation Plan

- Red/green `npm test -- src/app/AppFunctionalRates.test.tsx`.
- `npm run build`.
- Browser QA against local FastAPI + Vite with screenshot evidence.
- `git diff --check` for touched files.

## Risks

- Route-level and summary-level controls may duplicate labels; tests should
  scope queries to labeled regions.
- Issue list contract is narrower than batch detail and should be typed
  explicitly.

## Challenge Notes

This slice deepens Rates without expanding to export/approval/load-plan routes,
keeping the change reviewable.

## Decision

Proceed.
