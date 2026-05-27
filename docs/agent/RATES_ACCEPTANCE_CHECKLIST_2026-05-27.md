# Rates Acceptance Checklist - 2026-05-27

## Scope Reviewed

- Source spec: `docs/otm-workbench/gui/GUI_RATES_STUDIO_CONSOLIDATED_SPEC.md`.
- Current implementation surface: Rates frontend routes, Rates backend APIs,
  Rates tests, generated QA evidence, and module handoff notes.
- Data posture: synthetic-only fixtures, screenshots, and browser QA.

## Acceptance Criteria Status

| Criterion | Status | Evidence |
|---|---|---|
| `/rates` acts as hub, not full lifecycle host. | Accepted for current cycle | Hub has lifecycle destinations; deep work moved to route screens. |
| Batch rows open route-level detail pages with visible return paths. | Accepted | `/rates/batches/:batchId`, table detail, issues, artifacts, evidence, and handoff routes have return links. |
| Create batch opens a deliberate screen. | Accepted | `/rates/batches/new` exists and create navigates to batch overview. |
| Search supports backend-owned batch header fields and operators. | Partial | Search/status/domain filters exist; advanced operators and normalized backend filter metadata remain backlog. |
| Dedicated lifecycle task boundaries exist. | Accepted for current cycle | Stage, issues, CSV preview, export, approval, artifacts, evidence, Load Plan handoff, and table detail routes exist. |
| Artifact/evidence actions have dedicated review surfaces. | Accepted | `/artifacts` and `/evidence` routes exist; guarded download remains backend-owned. |
| Frontend does not own readiness/permission/rule truth. | Partial | Actions and artifacts use backend contracts; some visible readiness labels/counts are still frontend-shaped from backend data. |
| Functional QA covers happy, negative, out-of-order, and route recovery paths. | Partial | Functional tests cover create, filter, route recovery, review gates, download, approval, handoff, and state clearing; advanced operator/out-of-order guard matrix remains backlog. |
| No real client data appears in docs, UI fixtures, screenshots, or tests. | Accepted | QA data uses `qa.rates@example.test`, `OTM1`, and synthetic batch/table values. |

## Fresh Validation

Commands run:

```powershell
pytest tests/test_rates_batches.py -q
pytest tests/test_rates_summary.py -q
pytest tests/test_rates_csv_export_artifacts.py tests/test_rates_batch_approval.py -q
npm test -- src/app/AppFunctionalRates.test.tsx
npm run build
```

Results:

```text
tests/test_rates_batches.py: 8 passed
tests/test_rates_summary.py: 2 passed
tests/test_rates_csv_export_artifacts.py + tests/test_rates_batch_approval.py: 21 passed
AppFunctionalRates.test.tsx: 4 passed
frontend build: passed
```

Note: the first combined backend command timed out when run as one large group;
the same files passed when split into smaller commands.

## Accepted For Current Cycle

- Rates route family is now coherent enough to leave and return safely.
- Batch library, create, overview, stage, issues, table detail, CSV preview,
  export review, approval review, artifacts, evidence, and Load Plan handoff
  are route-level or route-adjacent task surfaces.
- Backend owns persisted artifacts, evidence, table rows, approval/export
  actions, and Load Plan package intake.

## Backlog Before Full Rates Completion

- Replace MVP client-side library filtering with normalized backend search
  metadata, operators, and pagination.
- Add route-level row detail/edit/delete only after backend row mutation
  contracts are designed.
- Add explicit backend eligibility/review endpoints for export and Load Plan
  handoff if the current action contracts become too coarse.
- Add Data Dictionary metadata summary to table detail.
- Expand out-of-order browser QA for blocked export/approval/handoff paths.

## Decision

Rates is accepted for the current delivery cycle and can stop being the active
module unless the user asks for the backlog items above immediately. The next
planned module slice should start with Assets.
