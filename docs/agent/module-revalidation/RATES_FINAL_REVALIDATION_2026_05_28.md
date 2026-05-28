# Rates Final Revalidation

**Status:** accepted for current UI phase
**Date:** 2026-05-28
**GitHub issue:** #187

## Scope Decision

Rates Studio is accepted for the current UI phase as a route-level tariff batch
lifecycle workspace with:

- Rates hub;
- batch library;
- batch creation;
- batch overview/detail;
- table staging;
- table detail;
- validation issues;
- CSV preview;
- export review;
- approval review;
- artifacts;
- evidence;
- Load Plan handoff.

The accepted scope follows `AGENTS.md`,
`docs/otm-workbench/gui/GUI_RATES_STUDIO_CONSOLIDATED_SPEC.md`,
`docs/agent/module-scope/RATES_STUDIO_SCOPE_REVIEW.md`, and
`docs/agent/wireframe-briefs/RATES_STUDIO_WIREFRAME_BRIEF.md`.

## Runtime Coverage Accepted

- `/rates` acts as a module hub and exposes lifecycle destinations instead of
  hosting every batch operation on one screen.
- `/rates/batches` supports the current searchable/filterable batch library.
- `/rates/batches/new` creates a synthetic rate batch through backend-owned
  module action contracts.
- `/rates/batches/:batchId` and child routes keep the selected batch, return
  paths, staged table detail, issue review, CSV preview, export review,
  approval review, artifacts, evidence, and Load Plan handoff coherent.
- Approval and export remain deliberate review routes, not lightweight inline
  list-row actions.
- Data Dictionary validation, table structure, CSV preview/export, artifacts,
  evidence, and Load Plan intake stay backend-owned for this phase.
- Synthetic-only data is used in tests and QA evidence.

## Evidence

Fresh automated validation on 2026-05-28:

```text
tests/test_rates_batches.py: 8 passed
tests/test_rates_summary.py: 2 passed
tests/test_rates_csv_export_artifacts.py + tests/test_rates_batch_approval.py: 21 passed
tests/test_rates_dictionary.py + tests/test_rates_csv_preview.py: 14 passed
tests/test_rates_batch_validation.py + tests/test_rates_batch_scenarios.py + tests/test_rates_batch_csv_preview.py: 20 passed
AppFunctionalRates.test.tsx: 4 passed
frontend build: passed with the existing Vite large chunk warning
```

Existing browser QA evidence from the Rates route-level completion slices:

```text
var/qa/rates-batch-library-search.png
var/qa/rates-library-new-routes.png
var/qa/rates-table-detail-route.png
var/qa/rates-route-level-batch-issues.png
var/qa/rates-route-level-review-screens.png
var/qa/rates-approval-export-review-gates.png
var/qa/rates-artifact-evidence-handoff-routes.png
var/qa/rates-route-recovery-lifecycle.png
```

Fresh browser screenshots were not captured in this closure slice. Any future
browser QA capture must first query `/api/v1/platform/navigation` on the same
runtime/session and reject evidence if excluded top-level modules appear.

Supporting docs:

```text
docs/agent/RATES_ACCEPTANCE_CHECKLIST_2026-05-27.md
docs/agent/TASK_CONTRACT_RATES_FINAL_REVALIDATION_2026_05_28.md
docs/otm-workbench/gui/GUI_RATES_STUDIO_CONSOLIDATED_SPEC.md
docs/agent/module-scope/RATES_STUDIO_SCOPE_REVIEW.md
docs/agent/wireframe-briefs/RATES_STUDIO_WIREFRAME_BRIEF.md
```

## Non-Blocking Follow-Ups

- Replace MVP client-side batch filtering with backend-owned advanced search
  metadata, operators, and pagination.
- Add row detail/edit/delete only after backend mutation contracts are
  designed.
- Add explicit backend eligibility/review endpoints for export and Load Plan
  handoff if current action contracts become too coarse.
- Add a visible Data Dictionary metadata summary to table detail.
- Expand browser QA for blocked export, approval, handoff, and artifact
  download paths when the shell is next refreshed.

## Blocking Gaps

No blocking Rates gaps remain for the current To-Be adaptation sequence.

## Handoff Decision

Close #187. The next tracked roadmap slice can move out of Rates unless the
user explicitly asks for one of the follow-up backlog items above.
