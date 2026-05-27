# Task Contract: Rates Route-Level Review Screens

## Objective

Add route-level Rates screens for CSV preview, export review, and approval
review.

## Original User Request

`siga com o próximo passo.`

## Interpreted Scope

- Implement `/rates/batches/:batchId/csv-preview`.
- Implement `/rates/batches/:batchId/export`.
- Implement `/rates/batches/:batchId/approve`.
- Keep review gates explicit before export and approval backend calls.
- Preserve the existing summary workspace behavior.

## Out Of Scope

- Backend changes.
- Artifact/evidence dedicated route screens.
- Load Plan handoff route.
- Server-side preview caching.

## Allowed Files Or Areas

- `frontend/src/modules/rates/RatesSummaryView.tsx`
- `frontend/src/app/AppFunctionalRates.test.tsx`
- `docs/agent/*`
- `docs/superpowers/plans/*`

## Protected Files Or Areas

- Backend Rates implementation.
- Other modules and unrelated dirty worktree changes.

## Acceptance Criteria

- Direct CSV preview route renders a preview workspace and can call preview.
- Direct export route renders explicit export review and only exports after
  confirmation.
- Direct approval route renders explicit approval review and only approves
  after a note and confirmation.
- Each route exposes `Back to Rates` and adjacent lifecycle navigation.
- Existing Rates functional tests continue to pass.

## Validation Plan

- Red/green `npm test -- src/app/AppFunctionalRates.test.tsx`.
- `npm run build`.
- Browser QA with local FastAPI + Vite and screenshot evidence.
- `git diff --check` for touched files.

## Risks

- Route-level workflow state should persist when navigating between adjacent
  review routes in the same component.
- Duplicate button names require scoped tests where necessary.

## Decision

Proceed.
