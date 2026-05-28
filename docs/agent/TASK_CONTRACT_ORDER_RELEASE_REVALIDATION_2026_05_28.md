# Task Contract: Order Release Revalidation

**Date:** 2026-05-28
**Status:** implementation follow-up required
**GitHub issue:** #205

## Objective

Revalidate Order Release Generator against the active To-Be route-level
generator workflow before starting the next implementation slice.

## Original User Request

The user asked to continue with the next roadmap step after Master Data
revalidation.

## Interpreted Scope

- Open the Order Release stabilization lane after Master Data.
- Compare current Order Release implementation against the active To-Be route
  family.
- Run fresh backend and frontend validation for templates, batches, XML
  preview, XML artifact generation, submit guard, and job tracking.
- Record accepted technical coverage and To-Be gaps.
- Create a follow-up implementation slice if the route-level To-Be is not yet
  satisfied.

## Out Of Scope

- Implementing route-level Order Release changes in this revalidation slice.
- Enabling real submit-to-OTM.
- Adding credential, connection, retry, or job-admin surfaces.
- Integration Mapping work.
- Workbench Assistant or shell work from parallel workstreams.

## Allowed Files Or Areas

- `docs/agent/TASK_CONTRACT_ORDER_RELEASE_REVALIDATION_2026_05_28.md`
- `docs/agent/module-revalidation/ORDER_RELEASE_FINAL_REVALIDATION_2026_05_28.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`
- GitHub issues #204, #205, and #206.

## Protected Files Or Areas

- `OTM_RESOURCES/`
- `outputs/`
- Integration Mapping files.
- Workbench Assistant files.
- unrelated frontend shell files currently modified by a parallel workstream.

## Acceptance Criteria

- Desired user outcome is restated before implementation.
- Backend/API and frontend behavior are validated for the current technical
  surface.
- Route-level To-Be gaps are documented without overstating acceptance.
- Follow-up issue exists for any blocking To-Be implementation gap.
- No protected data, real order data, local artifact paths, credentials, or
  production identifiers are committed.

## Validation Plan

```powershell
python -m pytest tests/test_order_release_generator_foundation.py tests/test_order_release_generator_batches.py -q
python -m pytest tests/test_order_release_generator_xml_preview.py tests/test_order_release_generator_xml_artifact.py -q
python -m pytest tests/test_order_release_generator_submit_guard.py tests/test_order_release_generator_jobs.py -q
npm test -- src/app/AppFunctionalOrderReleaseGenerator.test.tsx
npm test -- src/app/App.test.tsx -t "Order Release"
npm run build
```

## Risks

- Treating the passing technical tests as full To-Be acceptance would hide that
  the frontend still behaves as a single staged workspace.
- Order Release job tracking must remain module-owned evidence and not revive a
  separate top-level Jobs/Admin surface.
- Submit readiness must stay backend-owned and guarded.

## Challenge Notes

This is not a green-light-to-accept module slice. The current implementation is
healthy as a functional MVP, but the active To-Be requires route-level template
and batch workflows.

## Decision

Close #205 as revalidation complete, keep #204 open, and use #206 for the
route-level implementation slice.
