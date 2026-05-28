# Task Contract: Rates Table Detail Route

## Objective

Close the deferred Rates table-detail destination
`/rates/batches/:batchId/tables/:tableName` from the consolidated Rates spec.

## In Scope

- Add a backend endpoint for one staged rate table inside a scoped rate batch.
- Return table metadata, normalized staged rows, table-scoped issues, catalog
  macro-object, and catalog load-plan path.
- Render a route-level `Rate batch table detail` screen.
- Link table rows from the batch overview to the table detail route.
- Preserve visible return paths with `Back to Batch` and `Back to Rates`.

## Out of Scope

- Row edit/delete actions.
- Table-scoped validation action.
- Data Dictionary metadata expansion beyond catalog context already returned by
  Rates.

## Acceptance Criteria

- `GET /api/v1/modules/rates/batches/{batch_id}/tables/{table_name}` returns
  scoped table metadata and normalized rows.
- Missing tables return `404`.
- `/rates/batches/:batchId/tables/:tableName` renders table metadata, row
  values, and table-scoped issues.
- Existing Rates lifecycle routes still pass.
- Browser QA evidence is captured with synthetic data only.
