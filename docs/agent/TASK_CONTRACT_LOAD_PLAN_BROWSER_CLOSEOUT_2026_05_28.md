# Task Contract - Load Plan Browser Closeout

**Date:** 2026-05-28
**GitHub issue:** #207
**Status:** complete

## Objective

Close the Load Plan stabilization lane with fresh browser QA evidence after
route-level package recovery was implemented.

## Original User Request

Continue with the next roadmap step.

## Interpreted Scope

- Run the runtime navigation freshness gate before browser evidence.
- Run Load Plan browser QA against a fresh local backend/frontend pair.
- Fix QA-only blockers that prevent evidence from running against current API
  contracts.
- Fix any migration gap exposed by the fresh runtime when it is required by the
  current model.
- Record evidence and close the GitHub version lane.

## Out Of Scope

- Redesigning Load Plan visual layout.
- Real OTM/CSVUTIL execution.
- Integration Mapping development.
- Committing protected `OTM_RESOURCES/` data.

## Allowed Files Or Areas

- `frontend/scripts/functional-load-plan-browser.mjs`
- Load Plan-related Alembic migration files.
- Load Plan closeout docs under `docs/agent/`.

## Protected Files Or Areas

- `OTM_RESOURCES/`
- Unrelated Assistant, Integration Mapping, Settings, shell, or platform dirty
  worktree changes.

## Acceptance Criteria

- `tests/test_modules_navigation.py` passes before browser evidence.
- Live `/api/v1/platform/navigation` on the QA backend matches the current UI
  phase module set and excludes retired top-level modules.
- `npm run qa:functional:load-plan:browser` passes on the fresh runtime.
- Evidence path and runtime URLs are recorded.
- #207 is updated and closed.

## Validation Plan

- `python -m pytest tests/test_modules_navigation.py -q`
- `python -m alembic upgrade c5b9d3a1e6f2`
- `npm run qa:functional:load-plan:browser`
- Capture `var/qa/load-plan-route-closeout.png`

## Risks

- Browser evidence can be polluted by stale local servers.
- Local dirty workspace contains parallel Assistant changes; do not stage them.
- Screenshot evidence should be used for Load Plan/sidebar verification only.

## Challenge Notes

The first browser QA attempts exposed useful infrastructure defects: the QA
script was creating Rates batches outside the active context, and the Alembic
chain was missing the `load_plan_packages.domain_name` column required by the
current model.

## Decision

Fix the evidence blockers in the smallest possible scope, accept Load Plan
route recovery with browser QA passed, and close #207.
