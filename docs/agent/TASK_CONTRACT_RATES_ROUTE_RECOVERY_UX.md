# Task Contract: Rates Route Recovery UX

**Status:** active
**Date:** 2026-05-27

## Objective

Start Rates Studio completion against `10 / Rates Studio Deep Flow` by making
the current runtime screen expose route-level destinations and return paths for
the batch lifecycle.

## Original User Request

The user asked to continue after Settings final revalidation. The recorded next
module is Rates Studio.

## Interpreted Scope

- Add a first Rates runtime slice that reduces the current single-page harness
  feel without implementing every route family yet.
- Show backend-selected batch lifecycle destinations: batch library, create,
  batch overview, stage, issues, CSV preview/export, approval, artifacts,
  evidence, and Load Plan handoff.
- Add visible `Back to Cockpit` and `Back to Rates` recovery paths.
- Keep existing backend actions and data contracts intact.
- Add focused frontend tests, validation, and handoff notes.

## Out Of Scope

- Full route-level implementation for every Rates subroute.
- New backend Rates search APIs.
- CSVUTIL or Load Plan implementation changes.
- Approval/export behavior redesign beyond visible destination/recovery hints.
- Real client tariff data.

## Allowed Files Or Areas

- `frontend/src/modules/rates/RatesSummaryView.tsx`
- `frontend/src/app/AppFunctionalRates.test.tsx`
- `frontend/src/ui/layouts.css`
- `docs/agent/TASK_CONTRACT_RATES_ROUTE_RECOVERY_UX.md`
- `docs/superpowers/plans/2026-05-27-rates-route-recovery-ux.md`
- `docs/agent/VALIDATION_REPORT.md`
- `docs/agent/HANDOFF.md`

## Protected Files Or Areas

- Backend Rates logic unless a failing test proves a contract gap.
- Data Dictionary validation behavior.
- Load Plan runtime.
- Current Settings/Cockpit changes.

## Acceptance Criteria

- `/rates` displays a lifecycle navigation/recovery area.
- The area includes `Back to Cockpit`, `Open batch library`, and `Create rate
  batch` destinations.
- When a batch is selected, lifecycle links for stage, issues, CSV preview,
  export, approve, artifacts, evidence, and Load Plan handoff are visible.
- The selected lifecycle destinations are deterministic from the selected batch
  id.
- Existing Rates functional tests continue to pass.

## Validation Plan

```powershell
npm test -- src/app/AppFunctionalRates.test.tsx
npm run build
git diff --check
```

## Risks

- Links can imply implemented subroutes before the route family exists. Label
  the panel as route recovery/destination guidance and keep current actions
  unchanged.
- Do not replace backend-owned action disabled reasons with frontend guesses.

## Challenge Notes

This is a transition slice from the MVP one-page Rates workspace toward the
deep-flow route model, not the full Rates route-family delivery.

## Decision

Proceed with a focused Rates lifecycle destination and recovery panel.
