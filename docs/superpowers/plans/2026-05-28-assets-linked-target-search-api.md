# Assets Linked Target Search API Plan

## Goal

Add the backend contract needed for Assets Library linked target type search.

## Steps

1. Add failing backend tests for exact, `one_of`, `not_one_of`, and invalid
   linked target operators.
2. Implement linked target filtering with `AssetLink.asset_id` subqueries.
3. Preserve existing active-context scoped asset query behavior.
4. Run focused and full Assets backend tests.
5. Update validation and handoff docs.
