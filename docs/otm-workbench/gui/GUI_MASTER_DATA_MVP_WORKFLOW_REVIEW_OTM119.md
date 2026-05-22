# GUI Master Data MVP Workflow Review OTM-119

**Status:** completed for MVP workflow
**Date:** 2026-05-22
**Branch:** `codex/gui-foundation-integration-pr-plan`
**Linear:** `OTM-119`

## 1. Purpose

Record that the current Data Factory / Master Data GUI workflow has enough
backend contract coverage, frontend behavior, artifact parity, durable state,
and negative/out-of-order QA evidence to be treated as `MVP workflow done`.

This is not a `Module complete` declaration. Follow-up scope remains listed in
section 9.

## 2. Delivered Workflow

```text
select template
-> author/update/publish template from Catalog-backed tables and columns
-> validate template
-> build workbook
-> upload workbook
-> validate relationships
-> map records
-> build output
-> build OTM CSV files
-> export CSV ZIP package
-> recover batch/artifact state after route navigation
```

## 3. Backend Contracts

```text
GET  /api/v1/modules/master-data/templates
GET  /api/v1/modules/master-data/templates/{template_code}
POST /api/v1/modules/master-data/templates/drafts
PATCH /api/v1/modules/master-data/templates/{template_code}/draft
POST /api/v1/modules/master-data/templates/{template_code}/validate-definition
POST /api/v1/modules/master-data/templates/{template_code}/publish
POST /api/v1/modules/master-data/templates/{template_code}/versions
POST /api/v1/modules/master-data/templates/{template_code}/validate
POST /api/v1/modules/master-data/templates/{template_code}/build-workbook
POST /api/v1/modules/master-data/templates/{template_code}/batches
POST /api/v1/modules/master-data/batches/{batch_id}/validate-relationships
POST /api/v1/modules/master-data/batches/{batch_id}/map
POST /api/v1/modules/master-data/batches/{batch_id}/build-output
POST /api/v1/modules/master-data/batches/{batch_id}/build-csv
POST /api/v1/modules/master-data/batches/{batch_id}/export-csv-package
GET  /api/v1/modules/master-data/batches
GET  /api/v1/modules/master-data/batches/{batch_id}
GET  /api/v1/modules/master-data/batches/{batch_id}/artifacts
GET  /api/v1/modules/master-data/batches/{batch_id}/artifacts/{artifact_id}/download
```

The GUI does not infer lifecycle readiness, OTM table/column validity,
relationship validity, artifact availability, or download safety.

## 4. Artifact Parity

Backend tests cover OTM CSV shape for the MVP workflow:

```text
- table name on line 1
- CSV column header on line 2
- values after the header
- multiple OTM target tables exported as separate CSV files
- CSV ZIP package includes manifest.json plus csv/*.csv entries
- generated artifacts are registered with client-safe evidence
```

Date-column `exec alter session ...` behavior remains part of the global CSVUTIL
contract and should be expanded when a Master Data template with date fields is
introduced.

## 5. Authoring Coverage

Delivered:

```text
- template draft creation through backend contract
- Catalog macro-object, table, and column selection
- friendly labels
- USER_FIELD, FIXED_VALUE, and DEFAULT_VALUE mapping source types
- one input field mapped to multiple OTM target columns
- initial LOCATION -> LOCATION_ADDRESS relationship rule authoring
- definition validation and publish flow
- existing backend definition recovery into the Author stage
```

## 6. QA Evidence

Backend:

```text
python -m pytest tests\test_master_data_templates.py -q
```

Recent result:

```text
35 passed
```

Frontend:

```text
npm run test -- AppFunctionalMasterData.test.tsx
npm run lint
npm run build
```

Recent result:

```text
4 functional tests passed
lint passed
build passed
```

Browser:

```text
npm run qa:functional:master-data:browser
```

Recent journey:

```text
master-data-author-template-workbook-upload-output-export-route-recovery
```

## 7. Negative And Out-Of-Order Coverage

Delivered hardening:

```text
- missing artifact file appears as FILE_MISSING and does not expose download_url
- build-csv retry/double-click returns persisted CSVs without duplication
- export-csv-package retry/double-click returns existing artifact/manifest/evidence
- invalid workbook upload surfaces backend details and allows replacing the file
- route leave/return validates durable backend batch and artifact visibility
- child table removal clears dependent authoring state before re-add
```

## 8. Client Data Safety

The workflow uses synthetic region/location data only.

The GUI does not expose local artifact paths. Download URLs are backend-owned,
batch-scoped, client-safe, and hash-checked before file response.

## 9. Remaining Follow-Ups

These items remain outside the current MVP workflow and must stay tracked as
separate work before any `Module complete` claim:

```text
- Coordinate Quality GUI placement and workflow
- guarded Load Plan registration from exported packages
- direct OTM import / submit guardrails
- richer spreadsheet preview/editor only with backend-owned state
- date-field CSVUTIL alter-session coverage for date-bearing templates
- advanced batch history filters/pagination if operational volume requires it
```
