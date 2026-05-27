# Task Contract: Rates Library And New Batch Route Recovery

## Objective

Close the Rates revalidation gap where visible lifecycle links for
`/rates/batches` and `/rates/batches/new` existed but still rendered the generic
Rates hub instead of route-specific screens.

## In Scope

- Render `/rates/batches` as a route-level `Rate batch library` screen.
- Render `/rates/batches/new` as a route-level `New rate batch` screen.
- Keep visible return paths to Rates and the batch library.
- Reuse the existing backend-owned batch list and create batch contracts.
- Navigate a direct new-batch create result to `/rates/batches/:batchId`.

## Out of Scope

- Full advanced search operators from the long-form Rates spec.
- Scenario/template metadata expansion.
- Table detail route `/rates/batches/:batchId/tables/:tableName`.

## Acceptance Criteria

- Direct `/rates/batches` navigation shows a searchable library and `Create rate batch`.
- Direct `/rates/batches/new` navigation shows the create form and `Back to batch library`.
- Creating from `/rates/batches/new` posts to the backend and opens batch overview.
- Existing `/rates` embedded create and library flows continue to work.
- Functional Rates tests and frontend build pass.
- Browser QA evidence is captured.
