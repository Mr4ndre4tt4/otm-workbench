# Task Contract: Assets Library Search API

## Objective

Add the first backend-owned search/operator/pagination contract for the Assets
Library list endpoint.

## In Scope

- Extend `GET /api/v1/modules/assets/assets` with server-side pagination.
- Add text operators for asset name, description, module id, macro object, and
  OTM table metadata.
- Keep existing exact filters for type, category, status, scope, tag, module,
  macro object, and OTM table backwards compatible.
- Add backend tests for pagination, `contains`, `begins_with`, `one_of`,
  `not_one_of`, AND-combined filters, and invalid operators.
- Update validation and handoff docs.

## Out Of Scope

- Frontend search-builder UI.
- Link target type or target OTM version search.
- Asset version upload/link/archive behavior.
- Catalog Core, Evidence Hub, Admin Console, Developer Tools, or any excluded
  top-level navigation changes.

## Files

- `src/otm_workbench/modules/assets/routes.py`
- `tests/test_assets_library_assets.py`
- `docs/agent/VALIDATION_REPORT.md`
- `docs/agent/HANDOFF.md`

## Acceptance Criteria

- Existing asset list filters still work with their original query params.
- `page` and `page_size` return bounded rows with total count preserved.
- Text operators support case-insensitive `contains` and `begins_with`.
- List operators support comma-separated `one_of` and `not_one_of`.
- Empty filter values are ignored.
- Invalid operators return a structured `400` response.

## Validation

- Run the new focused backend tests first and confirm they fail before
  implementation.
- Run the full Assets Library backend test file after implementation.
- Run `git diff --check`.

## Risks

- Tag search is JSON-text backed today; this slice preserves the existing exact
  tag filter instead of expanding it into advanced operators.
- The frontend search-builder remains a follow-up slice.
