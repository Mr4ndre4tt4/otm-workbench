# Task Contract: Assets Linked Target Search API

## Objective

Add backend-owned filtering for the Assets Library `linked target type`
metadata field.

## In Scope

- Extend `GET /api/v1/modules/assets/assets` with `linked_target_type`.
- Support exact, `one_of`, and `not_one_of` matching through existing
  `AssetLink.link_type` records.
- Preserve existing list filters, pagination, and active-context scoping.
- Add backend tests for linked target filtering and invalid operators.

## Out Of Scope

- Frontend linked target type filter UI.
- Target OTM version support.
- New Asset or AssetLink model columns.
- Integration Mapping implementation work.

## Acceptance Criteria

- `linked_target_type=MODULE` returns assets linked to module targets.
- `linked_target_type_operator=one_of` accepts comma-separated link types.
- `linked_target_type_operator=not_one_of` excludes assets linked to the given
  type and keeps unlinked assets visible when otherwise scoped.
- Unsupported operators return `ASSET_SEARCH_INVALID_OPERATOR`.

## Validation

- `python -m pytest tests/test_assets_library_assets.py -k "linked_target_type"`
- `python -m pytest tests/test_assets_library_assets.py`
- `python -m pytest tests/test_assets_library_assets.py tests/test_assets_library_permissions.py tests/test_assets_library_foundation.py tests/test_assets_library_links.py tests/test_assets_library_versions.py`
- `git diff --check`
