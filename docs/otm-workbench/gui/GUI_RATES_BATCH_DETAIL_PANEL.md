# GUI Rates Batch Detail Panel

**Status:** implemented
**Branch:** `codex/gui-rates-batch-detail`

## Objective

Add the first object-level interaction to Rates Studio without duplicating
backend rules in the frontend.

## Backend Contracts

The Rates screen now uses:

```text
GET /api/v1/modules/rates/summary
GET /api/v1/modules/rates/batches/{batch_id}
```

The summary endpoint drives the list and metrics. The batch detail endpoint
drives the selected batch panel, including:

- batch status;
- scenario and domain;
- catalog macro object;
- staged tables;
- backend-owned available actions.

## GUI Behavior

Rates Studio now selects the first recent batch by default. Clicking another
batch in the list loads its detail panel.

The selected detail panel shows action buttons exactly as returned by the
backend. Disabled state and action labels are not inferred from frontend status
rules.

## Safety

The panel only renders aggregate and contract-safe values:

- table names;
- row counts;
- status labels;
- action metadata.

It does not render CSV row payloads, artifact file paths, or client-specific
source values.

## Validation

- `frontend/src/app/App.test.tsx` covers initial detail loading and selecting
  another batch.
- `tests/test_rates_batch_approval.py` covers the backend available-action
  contract for batch detail.
