# Task Contract - Load Plan Browser Closeout

**Date:** 2026-05-28
**GitHub issue:** #207
**Status:** promoted for clean PR validation

## Objective

Promote the Load Plan browser QA closeout patch to current `main` after
route-level package recovery was implemented.

## Original User Request

Continue with the next roadmap step.

## Interpreted Scope

- Run the runtime navigation freshness gate before browser evidence.
- Preserve the previously validated Load Plan browser QA script fixes.
- Fix QA-only blockers that prevent evidence from running against current API
  contracts.
- Fix any migration gap exposed by the fresh runtime when it is required by the
  current model.
- Record promotion evidence without importing the broader historical branch.

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
- The browser QA script passes syntax checks in this branch.
- Historical evidence path and runtime URLs remain recorded on #207.

## Validation Plan

- `python -m pytest tests/test_modules_navigation.py -q`
- `python -m alembic upgrade head`
- `node --check frontend/scripts/functional-load-plan-browser.mjs`

## Risks

- Browser evidence can be polluted by stale local servers.
- The historical screenshot should be used for Load Plan/sidebar verification
  only unless fresh browser QA is rerun from this clean branch.

## Challenge Notes

The first browser QA attempts exposed useful infrastructure defects: the QA
script was creating Rates batches outside the active context, and the Alembic
chain was missing the `load_plan_packages.domain_name` column required by the
current model.

## Decision

Promote the evidence blockers in the smallest possible scope. Keep #207 closed
unless clean-branch validation exposes a regression.
