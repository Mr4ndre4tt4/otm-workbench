# GUI Rates Summary View

**Status:** implemented MVP slice; superseded for future UX direction by `GUI_RATES_STUDIO_CONSOLIDATED_SPEC.md`
**Branch:** `codex/gui-rates-summary-view`

> 2026-05-26 update: the current `/rates` screen remains valid as backend
> contract evidence, but browser review found it combines overview, list,
> selected batch detail, staging, blockers, artifacts, and evidence on one long
> page. Use `GUI_RATES_STUDIO_CONSOLIDATED_SPEC.md` before implementing major Rates
> UI changes.

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

Batch selection is batch-workspace scoped. Selecting a different backend-owned
batch clears CSV preview rows, approval confirmation drafts, action feedback,
download state, and running action state from the previously selected batch.
Artifacts, evidence, tables, and available actions continue to reload from
backend queries keyed by the selected batch id.

Other module routes continue to use the shared placeholder template until their
read models are attached.

## Validation

- `frontend/src/app/App.test.tsx` verifies `/rates` calls
  `/api/v1/modules/rates/summary` with bearer auth and renders the summary.
- `frontend/src/app/AppFunctionalRates.test.tsx` covers create/stage/preview/export/download,
  approval, validation, and batch-switch recovery.
- `frontend/scripts/functional-rates-browser.mjs` covers the same browser path
  against local FastAPI + Vite with synthetic data only.
- `tests/test_rates_summary.py` validates the backend contract and client-safe
  blocker behavior.
