# Task Contract - Assets Batch And Checklist Link Targets

**Date:** 2026-05-28
**GitHub issue:** #199
**Status:** in progress

## Objective

Add backend-owned validation for Assets links to batch and checklist targets.

## Original User Request

Continue with the next roadmap step after closing Assets #198.

## Interpreted Scope

- Add BATCH and CHECKLIST as backend-owned asset link types.
- Validate BATCH targets against scoped `LoadPlanPackage` records.
- Validate CHECKLIST targets against scoped `CutoverChecklist` records by
  requiring the parent package to be visible in the user's active context.
- Preserve existing MODULE, MACRO_OBJECT, OTM_TABLE, ARTIFACT, and EVIDENCE
  behavior.
- Add focused backend tests for allowed and denied BATCH/CHECKLIST links.

## Out Of Scope

- Frontend visual redesign or target suggestion UI.
- Integration Mapping changes.
- New batch/checklist creation workflows.
- Relaxing artifact/evidence client-safe checks.

## Allowed Files Or Areas

- `src/otm_workbench/modules/assets/`
- `tests/test_assets_library_assets.py`
- `docs/agent/`

## Protected Files Or Areas

- `OTM_RESOURCES/`
- Integration Mapping files.
- Unrelated dirty workspace changes.

## Acceptance Criteria

- BATCH and CHECKLIST appear as seeded asset link classifications.
- Creating a BATCH link succeeds only for a scoped Load Plan package.
- Creating a CHECKLIST link succeeds only for a checklist whose parent package
  is scoped to the active user context.
- Hidden/out-of-context BATCH and CHECKLIST targets are rejected without leaking
  private target metadata.
- Existing artifact/evidence client-safe checks remain intact.

## Validation Plan

- `python -m pytest tests/test_assets_library_assets.py -k "batch_and_checklist_link_targets or rejected_when_outside_scope" -q`
- `python -m pytest tests/test_assets_library_assets.py -q`

## Risks

- BATCH is interpreted as Load Plan package for the current UI phase. If later
  modules introduce independent batch route families, they should add explicit
  target subtypes instead of broad frontend inference.

## Challenge Notes

The issue asks for backend-owned target types, not target suggestions. This
slice should stop at validation and seeded classifications.

## Decision

Proceed with scoped backend validation for Load Plan package and cutover
checklist targets.
