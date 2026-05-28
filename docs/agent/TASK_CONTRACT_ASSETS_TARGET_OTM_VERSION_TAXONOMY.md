# Task Contract - Assets Target OTM Version Taxonomy

**Date:** 2026-05-28
**GitHub issue:** #200
**Status:** in progress

## Objective

Decide and implement backend-owned validation for Assets `target_otm_version`
metadata.

## Original User Request

Continue with the next roadmap step after closing Assets #199.

## Interpreted Scope

- Use Oracle public Transportation and Global Trade Management release
  documentation as the release-label source of truth.
- Store accepted labels as an Assets classification taxonomy for the current UI
  phase.
- Validate create/update values against the taxonomy.
- Keep search/filter behavior compatible for stored values.
- Record the decision in repository governance docs.

## Out Of Scope

- Automatic crawling of Oracle documentation.
- Customer-specific release aliases.
- Schema-pack lifecycle or Developer Tools redesign.
- Integration Mapping work.

## Allowed Files Or Areas

- `src/otm_workbench/modules/assets/`
- `tests/test_assets_library_assets.py`
- `docs/agent/`

## Protected Files Or Areas

- `OTM_RESOURCES/`
- Integration Mapping files.
- Unrelated dirty workspace changes.

## Acceptance Criteria

- Decision is recorded in repo docs with source-of-truth rationale.
- `target_otm_version` create/update values are accepted only when backed by an
  active classification.
- Rejected values return backend validation details without customer-specific
  release values.
- Tests cover accepted and rejected create/update values.

## Validation Plan

- `python -m pytest tests/test_assets_library_assets.py -k "target_otm_version" -q`
- `python -m pytest tests/test_assets_library_assets.py -q`

## Risks

- Oracle release labels evolve quarterly. This slice seeds the current known
  26A/26B labels and makes future additions a classification update, not a code
  shape change.

## Challenge Notes

Do not add a broad platform release registry until multiple modules need richer
version metadata beyond label validation.

## Decision

Proceed with an Assets-owned classification taxonomy named
`asset_target_otm_version`.
