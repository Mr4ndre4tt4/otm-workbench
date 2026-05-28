# Task Contract: Assets Target OTM Version Search

## Objective

Implement GitHub issue #196 by adding a backend-owned `target_otm_version`
contract for Assets Library search.

## Original User Request

Continue with the next step after creating the GitHub version train for
`v0.3-assets-stabilization`.

## Interpreted Scope

- Treat #196 as the active delivery slice.
- Add `target_otm_version` as Asset-level metadata because it describes the OTM
  baseline an asset supports, not the uploaded file version or link target.
- Support create, update, serialize, list filter, and operator search.
- Add a database migration and focused backend tests first.
- Add frontend controls only after backend behavior is proven.

## Out Of Scope

- Integration Mapping changes.
- Real client data or customer-specific OTM baselines.
- Broad Assets redesign.
- Full Assets acceptance pass; that is tracked by #197.

## Allowed Files Or Areas

- `src/otm_workbench/models.py`
- `src/otm_workbench/modules/assets/`
- `tests/test_assets_library_assets.py`
- `migrations/versions/`
- Assets frontend files if backend tests pass.
- `docs/agent/HANDOFF.md` and `docs/agent/VALIDATION_REPORT.md` for handoff.

## Protected Files Or Areas

- `OTM_RESOURCES/`
- `outputs/`
- Integration Mapping implementation and docs unless explicitly requested.
- Assistant planning/source-index work from the parallel workspace.

## Acceptance Criteria

- Asset create accepts and serializes `target_otm_version`.
- Asset update can set or clear `target_otm_version`.
- Asset list supports `target_otm_version` plus text operators.
- Invalid operator handling remains consistent with existing asset search.
- Migration adds and removes the column/index.
- Tests prove the backend contract before frontend exposure.

## Validation Plan

- Run a focused failing test before implementation.
- Run the focused Assets backend tests after implementation.
- Run broader Assets backend tests if the schema/model change succeeds.
- Run frontend tests/build/browser QA only if frontend controls are added in
  this slice.

## Risks

- Existing local SQLite databases may need migration before using the new
  column.
- If future OTM version taxonomy needs official validation, this field may need
  classification metadata later. This slice stores a normalized safe token and
  does not assert Oracle support semantics.

## Challenge Notes

Implementing this as a frontend-only filter would violate backend-owned search
governance. Storing it on `AssetVersion` would confuse Workbench asset version
numbers with OTM product baselines.

## Decision

Proceed with a backend-first Asset metadata field and TDD.
