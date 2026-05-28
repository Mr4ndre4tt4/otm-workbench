# Task Contract - Load Plan Route-Level Workflows

**Date:** 2026-05-28
**GitHub issue:** #209
**Status:** in progress

## Objective

Make Load Plan / Cutover package operations addressable and recoverable through
the validated To-Be route family.

## Original User Request

Continue with the next roadmap step using small GitHub-visible slices.

## Interpreted Scope

- Derive selected package and active Load Plan operation from route URLs.
- Add visible route destinations for package, checklist, readiness, CSVUTIL,
  ZIP review, sequence, exports, go/no-go, and handoff.
- Preserve the existing backend-owned operational behavior and local workflow
  state.
- Add direct URL recovery coverage for a package operation route.

## Out Of Scope

- Splitting Cutover into a separate top-level module.
- Real OTM or CSVUTIL execution.
- Full visual redesign into separate route components.
- Integration Mapping changes.
- Browser screenshots unless the runtime navigation freshness gate passes.

## Allowed Files Or Areas

- `frontend/src/modules/load-plan/LoadPlanView.tsx`
- `frontend/src/app/AppFunctionalLoadPlan.test.tsx`
- Load Plan docs under `docs/agent/`

## Protected Files Or Areas

- `OTM_RESOURCES/`
- Integration Mapping files unless required for a minimal cross-module fix.
- Unrelated dirty worktree changes.

## Acceptance Criteria

- Direct URLs such as `/load-plan/packages/package_2/zip-review` select the
  expected package and active operation.
- Route destination links expose the active To-Be Load Plan route family.
- Existing Load Plan functional journey still passes.
- Focused backend Load Plan tests still pass.
- Handoff eligibility remains backend-owned and guarded.

## Validation Plan

- `npm test -- src/app/AppFunctionalLoadPlan.test.tsx`
- Focused backend Load Plan suite for package, checklist, readiness, CSVUTIL,
  ZIP analysis, review queue, sequence, export, go/no-go, handoff, and readiness
  export.
- `npm test -- src/app/App.test.tsx -t "Load Plan"`
- `npm run build`

## Risks

- Route links can imply separate page components that are not fully redesigned
  yet.
- Go/no-go and handoff share the current guarded handoff panel until a deeper
  visual route split is implemented.
- Browser evidence can be stale without the navigation freshness gate.

## Challenge Notes

This slice intentionally improves route recovery without pretending the full
To-Be visual decomposition is done.

## Decision

Proceed with a route-aware wrapper around the current Load Plan workspace and
keep deeper visual route decomposition as future backlog if needed.
