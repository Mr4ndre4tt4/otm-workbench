# Task Contract: Order Release Route-Level Workflows

**Date:** 2026-05-28
**Status:** implementation complete
**GitHub issue:** #206

## Objective

Make the existing Order Release Generator workflow addressable through the
route-level template and batch URLs required by the active To-Be scope.

## Original User Request

The user asked to continue with the next roadmap step.

## Interpreted Scope

- Keep the existing backend contracts and working generator behavior.
- Add route-aware frontend behavior for template, batch, rows, XML preview,
  artifacts, and submit-readiness URLs.
- Add visible route destinations and return paths from the Order Release
  workspace.
- Add functional coverage for direct route recovery.

## Out Of Scope

- Backend schema or API changes.
- Real submit-to-OTM.
- A separate top-level Jobs/Admin surface.
- Full visual redesign of the Order Release layout.
- Integration Mapping and Workbench Assistant changes.

## Allowed Files Or Areas

- `frontend/src/modules/order-release-generator/OrderReleaseGeneratorView.tsx`
- `frontend/src/app/AppFunctionalOrderReleaseGenerator.test.tsx`
- `docs/agent/TASK_CONTRACT_ORDER_RELEASE_ROUTE_LEVEL_WORKFLOWS.md`
- `docs/agent/HANDOFF.md`
- `docs/agent/VALIDATION_REPORT.md`

## Protected Files Or Areas

- `OTM_RESOURCES/`
- `outputs/`
- Integration Mapping files.
- Workbench Assistant files.
- unrelated frontend shell files modified by parallel workstreams.

## Acceptance Criteria

- Direct Order Release route URLs recover to the correct workflow state.
- The workspace exposes visible links for template, batch, rows, preview,
  artifacts, and submit-readiness destinations.
- Existing create batch, XML preview, artifact, submit guard, stale template
  switch, and template versioning behavior still passes.
- Backend Order Release tests still pass.
- Browser QA limitation is recorded if the existing script cannot reach the
  module.

## Validation Plan

```powershell
npm test -- src/app/AppFunctionalOrderReleaseGenerator.test.tsx
python -m pytest tests/test_order_release_generator_foundation.py tests/test_order_release_generator_batches.py tests/test_order_release_generator_xml_preview.py tests/test_order_release_generator_xml_artifact.py tests/test_order_release_generator_submit_guard.py tests/test_order_release_generator_jobs.py -q
npm test -- src/app/App.test.tsx -t "Order Release"
npm run build
npm run qa:functional:order-release:browser
```

## Risks

- This is a route-level recovery slice, not a full redesign. It makes the
  To-Be URLs usable while preserving the current component structure.
- The browser QA script depends on an existing local runtime and may fail before
  reaching the module if the shell/runtime is stale.

## Decision

Proceed with a focused route-level implementation. Keep deeper layout
separation, schema guidance, and advanced row-editor design as future slices if
needed.
