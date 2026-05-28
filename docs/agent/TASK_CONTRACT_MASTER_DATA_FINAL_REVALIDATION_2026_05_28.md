# Task Contract: Master Data Final Revalidation

**Date:** 2026-05-28
**Status:** implementation complete
**GitHub issue:** #203

## Objective

Revalidate Master Data / Data Factory against the active To-Be route-family
scope before starting any new Master Data implementation slice.

## Original User Request

The user asked to continue with the next roadmap step after Rates, Assets, and
GitHub governance closure.

## Interpreted Scope

- Confirm that the current Master Data route families still match the active
  scope for Data Factory, Template Builder, and Quality Tools.
- Run fresh backend and frontend validation for templates, operational batches,
  direct OTM import guardrails, coordinate quality, route recovery, artifacts,
  CSV/export, and Load Plan handoff behavior.
- Record accepted scope, non-blocking backlog, and any blocking gaps.
- Update GitHub issue #203 and PR #182 with validation evidence.

## Out Of Scope

- New Master Data product implementation.
- Reworking Template Builder, Data Factory, or Coordinate Quality UI.
- Direct OTM submission beyond existing guarded readiness and blocked-submit
  behavior.
- Fresh browser screenshot capture, because existing Master Data browser
  evidence already records the accepted route-family states and this slice is
  automated revalidation plus documentation.
- Integration Mapping, Workbench Assistant, and unrelated shell work from
  parallel workstreams.

## Allowed Files Or Areas

- `docs/agent/TASK_CONTRACT_MASTER_DATA_FINAL_REVALIDATION_2026_05_28.md`
- `docs/agent/module-revalidation/MASTER_DATA_FINAL_REVALIDATION_2026_05_28.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

## Protected Files Or Areas

- `OTM_RESOURCES/`
- `outputs/`
- Integration Mapping files.
- Workbench Assistant files.
- frontend shell files currently modified by a parallel workstream.

## Acceptance Criteria

- Desired user outcome is restated before implementation.
- Backend/API and frontend route behavior agree for current Master Data scope.
- Happy, negative, out-of-order, route recovery, artifact/export, direct OTM
  import guard, and Load Plan handoff paths are covered or explicitly deferred.
- Data Dictionary dependency behavior remains clear and backend-owned.
- Existing browser QA evidence is named, and lack of fresh screenshots is
  explicit.
- #203 is updated and closed without changing product behavior.

## Validation Plan

```powershell
python -m pytest tests/test_master_data_direct_otm_import_guard.py -q
python -m pytest tests/test_coordinate_quality_api.py tests/test_coordinate_quality_engine.py -q
python -m pytest tests/test_master_data_templates.py -q
npm test -- src/app/AppFunctionalMasterData.test.tsx src/app/AppFunctionalCoordinateQuality.test.tsx
npm test -- src/app/App.test.tsx -t "Master Data"
npm run build
```

## Risks

- Existing browser screenshots were not recaptured in this slice; stale-runtime
  protection remains mandatory before any future browser evidence.
- Master Data still has deeper backlog around governed direct OTM submit,
  audited spreadsheet editing, advanced coordinate diagnostics, and deeper Load
  Plan handoff depth.
- Parallel Integration Mapping and Assistant changes are present in the
  worktree and must not be committed as part of this slice.

## Challenge Notes

The correct next action is revalidation, not implementation. Master Data has a
large existing surface, and moving directly into feature work would risk
reviving the old overloaded workflow model.

## Decision

Proceed with documentation/GitHub closure only. Master Data / Data Factory is
accepted for the current UI phase, with follow-up slices to be created only for
specific gaps identified after this revalidation.
