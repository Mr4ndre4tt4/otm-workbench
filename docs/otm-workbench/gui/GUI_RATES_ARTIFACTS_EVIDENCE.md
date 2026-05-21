# GUI Rates Artifacts And Evidence Panels

**Status:** implemented
**Branch:** `codex/gui-rates-artifacts-evidence`

## Objective

Attach batch-level artifacts and evidence panels to Rates Studio while keeping
the GUI constrained to client-safe metadata.

## Backend Contracts

The selected batch panel now consumes:

```text
GET /api/v1/modules/rates/batches/{batch_id}/artifacts
GET /api/v1/modules/rates/batches/{batch_id}/evidence
```

## GUI Behavior

When a batch is selected, Rates Studio loads:

- artifact file name;
- artifact type;
- content type;
- size in bytes;
- sensitivity level;
- evidence type;
- evidence status;
- evidence artifact link indicator;
- client-safe/internal indicator.

The panels refresh automatically when the selected batch changes.

## Safety

The GUI does not render:

- local artifact file paths;
- CSV row payloads;
- manifest internals;
- evidence `summary_json` contents;
- client-specific source values.

## Validation

- `frontend/src/app/App.test.tsx` validates both panels in the Rates route.
- `tests/test_rates_csv_export_artifacts.py` validates backend artifact,
  evidence, download, hash, and path-safety behavior.
