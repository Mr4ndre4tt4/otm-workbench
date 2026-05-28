# Task Contract - Load Plan Final Revalidation

**Date:** 2026-05-28
**GitHub issue:** #208
**Status:** complete; implementation follow-up required

## Objective

Revalidate Load Plan / Cutover against the active To-Be package lifecycle before
continuing module development.

## Original User Request

Continue with the next roadmap step using GitHub-versioned, smaller delivery
slices and current project governance.

## Interpreted Scope

- Revalidate the existing backend/API and frontend behavior for package intake,
  checklist, readiness, CSVUTIL, ZIP review, review queue, sequence, exports,
  go/no-go, and handoff.
- Compare the current UI shape with the validated route family in the Load Plan
  scope review and Michelangelo brief.
- Record any blocking To-Be gaps and open a follow-up issue instead of silently
  expanding the revalidation slice.

## Out Of Scope

- Real OTM or CSVUTIL execution.
- Splitting Cutover into a separate top-level module.
- Reworking Integration Mapping.
- Committing protected local `OTM_RESOURCES/` files or real package data.
- Accepting browser screenshots without the runtime navigation freshness gate.

## Allowed Files Or Areas

- Load Plan documentation under `docs/agent/`.
- GitHub issues and PR comments for the active delivery lane.
- Validation evidence records.

## Protected Files Or Areas

- `OTM_RESOURCES/`.
- Integration Mapping source and docs, except minimal cross-module references.
- Unrelated dirty worktree changes from parallel assistant/user work.

## Acceptance Criteria

- Validation commands and exact results are recorded.
- Desired Load Plan To-Be route family is compared with current implementation.
- Blocking gaps are linked to a GitHub follow-up issue.
- Handoff and validation docs are updated.
- No real client data or protected local resources are included.

## Validation Plan

- Run focused backend pytest slices for Load Plan package, checklist, readiness,
  CSVUTIL, ZIP review, review queue, sequence, export, go/no-go, and handoff.
- Run focused frontend functional tests for Load Plan.
- Run the broad frontend build.
- Defer browser screenshots unless live navigation freshness can be proven.

## Risks

- The existing implementation can pass functional tests while remaining too
  stacked for the route-level To-Be workflow.
- Browser QA evidence can be stale if the local backend still exposes excluded
  top-level modules.
- Handoff must remain backend-owned and eligibility-gated.

## Challenge Notes

The technical foundation is healthy, but the current UI still uses local stage
state instead of deriving package operations from route-level URLs. Treating
that as complete would repeat the earlier sidebar/runtime-evidence failure
mode.

## Decision

Close #208 as a revalidation slice with follow-up #209 for route-level package
workflow recovery.
