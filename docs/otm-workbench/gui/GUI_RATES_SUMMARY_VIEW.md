# GUI Rates Summary View

**Status:** implemented
**Branch:** `codex/gui-rates-summary-view`

## Objective

Replace the generic `/rates` module placeholder with the first useful
backend-driven Rates Studio view.

## Backend Contract

The view consumes:

```text
GET /api/v1/modules/rates/summary
```

The frontend renders only fields already exposed by this summary contract:

- module title and description;
- module-level available actions;
- count cards;
- recent rate batches;
- open blockers;
- batch status and safe aggregate counts.

No batch payload rows, CSV contents, artifact file paths, or client-specific
values are required by the GUI.

## GUI Behavior

When the user opens `/rates`, the shared routing foundation detects the backend
navigation item with `id = rates` and renders `RatesSummaryView`.

The screen includes:

- reusable page header;
- count metrics;
- recent batch list;
- blockers panel;
- backend-owned available action buttons.

Other module routes continue to use the shared placeholder template until their
read models are attached.

## Validation

- `frontend/src/app/App.test.tsx` verifies `/rates` calls
  `/api/v1/modules/rates/summary` with bearer auth and renders the summary.
- `tests/test_rates_summary.py` validates the backend contract and client-safe
  blocker behavior.
