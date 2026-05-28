# Task Contract: Rates Approval And Export Review UX

**Status:** active
**Date:** 2026-05-27

## Objective

Continue Rates Studio completion by making approval and export visually gated
review steps instead of lightweight inline actions.

## Original User Request

The user asked to continue after the Rates route recovery slice. The recorded
next highest-value slice is approval/export review gating.

## Interpreted Scope

- Keep existing backend action contracts intact.
- Add an explicit approval review block before confirming approval.
- Add an explicit CSV export review block before executing export.
- Require `Confirm export` before calling the export endpoint.
- Keep existing create, stage, preview, download, approve, and validate flows
  working.

## Out Of Scope

- New backend readiness endpoints.
- Full `/rates/batches/:batchId/approve` or `/export` route implementation.
- Changes to Rates validation, CSV generation, or approval backend logic.
- Real client tariff data.

## Allowed Files Or Areas

- `frontend/src/modules/rates/RatesSummaryView.tsx`
- `frontend/src/app/AppFunctionalRates.test.tsx`
- `frontend/src/ui/layouts.css`
- `docs/agent/TASK_CONTRACT_RATES_APPROVAL_EXPORT_REVIEW_UX.md`
- `docs/superpowers/plans/2026-05-27-rates-approval-export-review-ux.md`
- `docs/agent/VALIDATION_REPORT.md`
- `docs/agent/HANDOFF.md`

## Protected Files Or Areas

- Backend Rates implementation unless tests expose a real contract gap.
- Load Plan handoff behavior.
- Settings/Cockpit code.

## Acceptance Criteria

- Approval confirmation renders a `Rate approval review` area with batch,
  scenario, status, table count, and domain.
- CSV export requires a `Rate export review` area and `Confirm export` click
  before the backend export endpoint is called.
- Export review exposes batch, scenario, table count, preview count, and
  client-safe artifact intent.
- Existing functional Rates journey still passes.

## Validation Plan

```powershell
npm test -- src/app/AppFunctionalRates.test.tsx
npm run build
git diff --check
```

## Risks

- The review panel must not claim readiness beyond the backend-owned action
  states already returned.
- Do not hide disabled reasons or replace backend action gating with frontend
  inference.

## Challenge Notes

This slice improves safety on the current page while later slices can turn
approve/export into dedicated route-level screens.

## Decision

Proceed with a focused frontend review-gating slice.
