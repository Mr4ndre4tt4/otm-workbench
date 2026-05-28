# Master Data Final Revalidation

**Status:** accepted for current UI phase
**Date:** 2026-05-28
**GitHub issue:** #203
**Version issue:** #202

## Scope Decision

Master Data / Data Factory is accepted for the current UI phase as one module
with three separate route families:

- Data Factory;
- Template Builder;
- Quality Tools.

The accepted scope follows `AGENTS.md`,
`docs/agent/module-scope/MASTER_DATA_DATA_FACTORY_SCOPE_REVIEW.md`,
`docs/otm-workbench/gui/GUI_MASTER_DATA_DATA_FACTORY_REDESIGN_SPEC.md`,
`docs/otm-workbench/gui/GUI_MASTER_DATA_REDESIGN_COMPLETION_REVIEW_2026_05_26.md`,
and `docs/agent/wireframe-briefs/MASTER_DATA_DATA_FACTORY_WIREFRAME_BRIEF.md`.

## Runtime Coverage Accepted

- `/master-data` acts as the module hub and separates operational, authoring,
  and quality jobs.
- `/master-data/factory` supports published-template consumption and recent
  operational batch discovery.
- `/master-data/factory/templates/:templateCode` supports published template
  detail, workbook/editor preparation, and backend-owned template actions.
- `/master-data/factory/batches/:batchId` supports batch execution detail,
  relationship validation, mapping, output records, CSV files, export package,
  guarded artifact download, direct OTM import guardrails, and Load Plan
  handoff.
- `/master-data/template-builder` and child routes support draft/published
  template authoring, detail, edit, copy, delete/retire impact review,
  validation, publish, and version behavior.
- `/master-data/quality`, `/master-data/quality/lat-lon`, and
  `/master-data/quality/lat-lon/batches/:batchId` support coordinate quality
  validation, persisted result review, export, and direct route recovery.
- The frontend does not infer template validity, Data Dictionary table validity,
  export eligibility, direct-import eligibility, Load Plan readiness, or
  coordinate quality result status.
- Synthetic-only data is used in tests and QA evidence.

## Evidence

Fresh automated validation on 2026-05-28:

```text
tests/test_master_data_direct_otm_import_guard.py: 5 passed
tests/test_coordinate_quality_api.py + tests/test_coordinate_quality_engine.py: 15 passed
tests/test_master_data_templates.py: 58 passed
AppFunctionalMasterData.test.tsx + AppFunctionalCoordinateQuality.test.tsx: 7 passed
App.test.tsx - Master Data: 4 passed, 26 skipped
frontend build: passed with the existing Vite large chunk warning
```

Known non-failing warning:

```text
jsdom printed "Not implemented: navigation to another Document" during the
functional frontend run for download/navigation behavior that browser QA owns.
```

Existing browser QA evidence from the Master Data redesign completion slice:

```text
output/gui-qa/master-data/01-master-data-hub.png
output/gui-qa/master-data/02-template-builder-entry.png
output/gui-qa/master-data/02-template-builder-search.png
output/gui-qa/master-data/02-template-builder-detail.png
output/gui-qa/master-data/02-template-builder-copy.png
output/gui-qa/master-data/02-template-builder-copy-created.png
output/gui-qa/master-data/02-template-builder-edit.png
output/gui-qa/master-data/02-template-builder-retire.png
output/gui-qa/master-data/02-template-builder-new.png
output/gui-qa/master-data/03-data-factory-entry.png
output/gui-qa/master-data/04-template-detail-regions-basic.png
output/gui-qa/master-data/05-batch-detail-input.png
output/gui-qa/master-data/06-batch-detail-validated.png
output/gui-qa/master-data/07-batch-detail-csv-package.png
output/gui-qa/master-data/08-batch-detail-load-plan.png
output/gui-qa/master-data/09-quality-tools-hub.png
output/gui-qa/master-data/10-lat-lon-validator.png
output/gui-qa/master-data/11-lat-lon-batch-detail.png
output/gui-qa/master-data/12-lat-lon-export.png
```

Fresh browser screenshots were not captured in this closure slice. Any future
browser QA capture must first query `/api/v1/platform/navigation` on the same
runtime/session and reject evidence if excluded top-level modules appear.

## Non-Blocking Follow-Ups

- Governed direct OTM submission remains future scope until connection,
  credential, capability, audit, retry/job, and Oracle transport governance
  exist.
- Deeper audited spreadsheet editing remains future scope.
- Advanced Coordinate Quality map diagnostics and external provider governance
  remain future scope.
- Dedicated Template Builder retire/delete backend mutation can be separated
  from the current impact-review surface.
- Copy-option granularity in the backend version/copy endpoint remains backlog.
- Deeper Load Plan export/handoff behavior may be expanded in a later Load Plan
  slice.
- Larger scenario-pack coverage for additional Master Data families remains
  backlog.

## Blocking Gaps

No blocking Master Data / Data Factory gaps remain for the current To-Be
adaptation sequence.

## Handoff Decision

Close #203. Keep #202 open as the Master Data stabilization lane until the
next concrete follow-up slices are either created or explicitly deferred.
