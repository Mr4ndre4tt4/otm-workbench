# Task Contract: Rates Final Revalidation

**Date:** 2026-05-28
**Status:** implementation complete

## Objective

Revalidate and close GitHub issue #187 for Rates Studio against the active
To-Be batch lifecycle flow before moving to the next roadmap slice.

## Original User Request

The user asked to continue with the next roadmap step.

## Interpreted Scope

- Confirm that the existing Rates route family still matches the active
  consolidated Rates specification and wireframe brief.
- Run fresh backend and frontend validation for Rates batch lifecycle,
  Data Dictionary validation, CSV preview/export, approval, artifacts,
  evidence, and Load Plan handoff contracts.
- Record a current closure note and close #187 without adding new product
  behavior.

## Out Of Scope

- New Rates implementation beyond revalidation and documentation.
- Reworking client-side search into backend-owned advanced search metadata.
- Adding row mutation/edit/delete contracts.
- Fresh browser screenshot capture, because existing Rates browser QA evidence
  already records the accepted route-level states and this slice is GitHub/docs
  closure plus automated revalidation.
- Integration Mapping, Workbench Assistant, and unrelated shell changes from
  parallel workstreams.

## Allowed Files Or Areas

- `docs/agent/TASK_CONTRACT_RATES_FINAL_REVALIDATION_2026_05_28.md`
- `docs/agent/module-revalidation/RATES_FINAL_REVALIDATION_2026_05_28.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

## Protected Files Or Areas

- `OTM_RESOURCES/`
- `outputs/`
- Integration Mapping files.
- Workbench Assistant files.
- frontend shell files currently modified by a parallel workstream.

## Acceptance Criteria

- Desired user outcome is revalidated against the active To-Be flow.
- Backend/API and frontend route behavior agree for the current lifecycle
  surface.
- Happy, blocked, out-of-order/recovery-adjacent, artifact, approval, and
  handoff paths are either covered by automated tests or explicitly deferred.
- OTM table dependency behavior remains tied to Data Dictionary validation.
- Existing browser QA evidence is named and any lack of fresh screenshots is
  explicit.
- #187 is updated and closed without changing product behavior.

## Validation Plan

```powershell
python -m pytest tests/test_rates_batches.py -q
python -m pytest tests/test_rates_summary.py -q
python -m pytest tests/test_rates_csv_export_artifacts.py tests/test_rates_batch_approval.py -q
python -m pytest tests/test_rates_dictionary.py tests/test_rates_csv_preview.py -q
python -m pytest tests/test_rates_batch_validation.py tests/test_rates_batch_scenarios.py tests/test_rates_batch_csv_preview.py -q
npm test -- src/app/AppFunctionalRates.test.tsx
npm run build
```

## Risks

- Advanced backend search metadata, pagination, and route-level row mutation
  remain backlog items, not blockers for the current To-Be adaptation sequence.
- Browser screenshots were not recaptured in this closure slice; stale-runtime
  protection remains mandatory for any future browser QA capture.
- Parallel Integration Mapping and Assistant changes are present in the
  worktree and must not be committed as part of this slice.

## Decision

Proceed with documentation/GitHub closure only. Rates is accepted for the
current UI phase, with backlog items tracked outside this closure slice.
