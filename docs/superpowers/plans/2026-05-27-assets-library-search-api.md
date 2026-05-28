# Assets Library Search API Plan

## Goal

Implement the backend-owned search/operator/pagination baseline for
`GET /api/v1/modules/assets/assets`.

## Steps

1. Add failing backend tests for pagination, text operators, combined filters,
   and invalid operators.
2. Add route helpers that normalize operators and comma-separated values.
3. Apply text filters to name, description, module id, macro object, and OTM
   table while preserving existing exact filters.
4. Add bounded pagination with full filtered total.
5. Run focused and full backend validation.
6. Update handoff and validation docs.
