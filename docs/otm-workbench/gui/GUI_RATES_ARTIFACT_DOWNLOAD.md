# GUI Rates Artifact Download

**Status:** implemented
**Branch:** `codex/gui-rates-artifact-download`

## Objective

Add a guarded artifact download affordance to Rates Studio without exposing
local file paths or constructing download routes in the frontend.

## Backend Contract

`GET /api/v1/modules/rates/batches/{batch_id}/artifacts` now includes
`download_url` per artifact item.

The download itself still uses the existing protected endpoint:

```text
GET /api/v1/modules/rates/batches/{batch_id}/artifacts/{artifact_id}/download
```

## GUI Behavior

Rates Studio renders a `Download` button for artifacts that include
`download_url`.

On click, the GUI:

- calls `download_url` with bearer authentication;
- reads the response blob;
- uses the server-provided filename when available;
- starts a browser download;
- shows a success or error message.

## Safety

The GUI does not render artifact local paths. The backend remains responsible
for:

- artifact ownership by batch;
- file existence checks;
- hash validation;
- audit logging;
- filename/content-type response metadata.

## Validation

- Frontend test verifies authenticated download call and browser download
  affordance.
- Backend artifact export suite verifies download URL, protected download,
  audit, hash mismatch, and path-safety behavior.

Commands executed:

```text
cd frontend
npm run test
npm run lint
npm run build
cd ..
python -m pytest tests\test_rates_csv_export_artifacts.py -q
python -m ruff check src tests
```
