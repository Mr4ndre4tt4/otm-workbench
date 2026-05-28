# Order Release Revalidation

**Status:** implementation follow-up required
**Date:** 2026-05-28
**GitHub issue:** #205
**Version issue:** #204
**Follow-up implementation issue:** #206

## Scope Decision

Order Release Generator has a healthy backend-first functional foundation, but
it is not yet accepted as complete for the active To-Be route-level UI phase.

The accepted technical foundation covers:

- backend-owned templates;
- backend-owned batch creation and validation;
- template-guided row editing in the current UI;
- XML preview generation;
- XML artifact generation and guarded download;
- guarded direct OTM submit behavior;
- job tracking as module evidence.

The blocking To-Be gap is information architecture: the current frontend still
concentrates template authoring, versioning, template list, active batch, row
editor, XML preview, artifact generation, submit guard, and recent batches in a
single staged workspace at `/order-release-generator`.

The active To-Be requires route-level workflows from
`docs/otm-workbench/gui/GUI_ORDER_RELEASE_GENERATOR_CONSOLIDATED_SPEC.md` and
`docs/agent/wireframe-briefs/ORDER_RELEASE_GENERATOR_WIREFRAME_BRIEF.md`.

## Runtime Coverage Validated

Fresh validation confirms that the current implementation still supports:

- template list and creation;
- template version creation;
- batch creation from a selected template;
- required/optional field defaults in the row editor;
- invalid row blockers;
- XML preview generation;
- XML artifact generation;
- guarded artifact download;
- direct OTM submit guard;
- stale template switch clearing batch, preview, artifact, and submit state;
- recent batch recovery;
- backend job-tracking contracts.

## Fresh Validation

Commands run on 2026-05-28:

```powershell
python -m pytest tests/test_order_release_generator_foundation.py tests/test_order_release_generator_batches.py -q
python -m pytest tests/test_order_release_generator_xml_preview.py tests/test_order_release_generator_xml_artifact.py -q
python -m pytest tests/test_order_release_generator_submit_guard.py tests/test_order_release_generator_jobs.py -q
npm test -- src/app/AppFunctionalOrderReleaseGenerator.test.tsx
npm test -- src/app/App.test.tsx -t "Order Release"
npm run build
```

Results:

```text
tests/test_order_release_generator_foundation.py + tests/test_order_release_generator_batches.py: 23 passed
tests/test_order_release_generator_xml_preview.py + tests/test_order_release_generator_xml_artifact.py: 8 passed
tests/test_order_release_generator_submit_guard.py + tests/test_order_release_generator_jobs.py: 4 passed
AppFunctionalOrderReleaseGenerator.test.tsx: 3 passed
App.test.tsx - Order Release: 1 passed, 29 skipped
frontend build: passed with existing Vite large chunk warning
```

Known non-failing warning:

```text
jsdom printed "Not implemented: navigation to another Document" during the
functional frontend run for download/navigation behavior that browser QA owns.
```

## Required Follow-Up

Issue #206 tracks the implementation slice:

```text
[Slice]: Order Release route-level template and batch workflows
```

The route-level target includes:

```text
/order-release-generator
/order-release-generator/templates/new
/order-release-generator/templates/:templateId
/order-release-generator/templates/:templateId/versions
/order-release-generator/batches/new
/order-release-generator/batches/:batchId
/order-release-generator/batches/:batchId/rows
/order-release-generator/batches/:batchId/preview
/order-release-generator/batches/:batchId/artifacts
/order-release-generator/batches/:batchId/submit-readiness
```

## Non-Blocking Follow-Ups

- Deeper schema-pack guidance for official Release/ReleaseLine paths.
- DBXML artifact variants beyond the current XML/DBXML-safe artifact path.
- Submit-to-OTM capability only after governed connection, credentials,
  capability, audit, retry/job, and Oracle transport governance exist.
- More advanced row editor layouts for realistic multi-line releases.

## Blocking Gaps

- Route-level template and batch workflows are not implemented yet.
- Preview, artifacts, and submit readiness are not dedicated route states yet.
- The hub still carries too much lifecycle and authoring responsibility.

## Handoff Decision

Close #205 as revalidation complete. Keep #204 open and continue with #206.
