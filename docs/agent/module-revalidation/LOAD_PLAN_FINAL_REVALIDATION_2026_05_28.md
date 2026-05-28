# Load Plan Final Revalidation

**Date:** 2026-05-28
**GitHub issues:** #207, #208, #209
**Status:** foundation revalidated; To-Be route-level follow-up required

## Desired Outcome

Load Plan / Cutover should let a cutover lead take source packages through a
governed package lifecycle: package review, checklist, readiness, CSVUTIL, ZIP
review, sequence, exports, go/no-go, and backend-eligible handoff. Cutover stays
inside Load Plan, not as a separate top-level module.

## Source Baseline

- `docs/agent/module-scope/LOAD_PLAN_CUTOVER_SCOPE_REVIEW.md`
- `docs/agent/wireframe-briefs/LOAD_PLAN_CUTOVER_WIREFRAME_BRIEF.md`
- `docs/otm-workbench/gui/GUI_LOAD_PLAN_CUTOVER_CONSOLIDATED_SPEC.md`
- `docs/otm-workbench/gui/GUI_LOAD_PLAN_VIEW.md`

## Current Implementation Finding

The backend/API foundation and existing functional journey are healthy. The
frontend currently exposes the Load Plan lifecycle through one workspace with
stage buttons and local state. That supports the operational sequence, but it
does not yet satisfy the To-Be route-recovery expectation for package operation
URLs.

Required To-Be route family:

```text
/load-plan
/load-plan/packages
/load-plan/packages/:packageId
/load-plan/packages/:packageId/checklist
/load-plan/packages/:packageId/readiness
/load-plan/packages/:packageId/csvutil
/load-plan/packages/:packageId/zip-review
/load-plan/packages/:packageId/sequence
/load-plan/packages/:packageId/exports
/load-plan/packages/:packageId/go-no-go
/load-plan/packages/:packageId/handoff
```

Follow-up:

- #209 `[Slice]: Load Plan route-level package workflows`

## Validation Run

```powershell
python -m pytest tests/test_load_plan_package_intake.py -q
python -m pytest tests/test_load_plan_cutover_checklist.py -q
python -m pytest tests/test_load_plan_cutover_readiness.py -q
python -m pytest tests/test_load_plan_csvutil_builder.py -q
python -m pytest tests/test_load_plan_zip_analysis.py -q
python -m pytest tests/test_load_plan_sequence_blockers.py -q
python -m pytest tests/test_load_plan_review_queue.py tests/test_load_plan_review_decisions.py -q
python -m pytest tests/test_load_plan_cutover_package_export.py tests/test_load_plan_cutover_go_no_go.py tests/test_load_plan_cutover_handoff.py tests/test_load_plan_readiness_export.py -q
npm test -- src/app/AppFunctionalLoadPlan.test.tsx
npm test -- src/app/App.test.tsx -t "Load Plan"
npm run build
```

## Results

```text
tests/test_load_plan_package_intake.py: 23 passed
tests/test_load_plan_cutover_checklist.py: 13 passed
tests/test_load_plan_cutover_readiness.py: 9 passed
tests/test_load_plan_csvutil_builder.py: 16 passed
tests/test_load_plan_zip_analysis.py: 12 passed
tests/test_load_plan_sequence_blockers.py: 13 passed
tests/test_load_plan_review_queue.py + tests/test_load_plan_review_decisions.py: 16 passed
tests/test_load_plan_cutover_package_export.py + tests/test_load_plan_cutover_go_no_go.py + tests/test_load_plan_cutover_handoff.py + tests/test_load_plan_readiness_export.py: 25 passed
AppFunctionalLoadPlan.test.tsx: 1 passed
App.test.tsx - Load Plan: 1 passed, 29 skipped
frontend build: passed with existing Vite large chunk warning
```

## Browser QA

Fresh browser screenshots were not captured for #208. This revalidation does
not make a visual acceptance claim. Any future browser evidence must first pass
the `/api/v1/platform/navigation` runtime freshness gate and reject stale
screenshots that expose excluded top-level modules.

## Accepted

- Package intake, detail, and source module metadata are backed by focused API
  coverage.
- Cutover checklist creation, item evidence updates, readiness generation, and
  CSVUTIL artifact build are covered.
- ZIP analysis, review queue decisions, sequence blockers, readiness export,
  cutover package export, go/no-go, and handoff eligibility are covered.
- Handoff remains backend-owned and guarded.
- No protected `OTM_RESOURCES/` files or real client package data are included.

## Not Yet Accepted

- Route-level package operation recovery is not complete in the frontend.
- The current UI is still a stage-based workspace rather than deliberate
  route-level screens for each critical operation.
- Browser visual acceptance is deferred until a fresh runtime passes the
  navigation freshness gate.

## Decision

#208 is complete as a revalidation slice. Continue #207 through #209 before
accepting Load Plan / Cutover as To-Be route-aligned.
