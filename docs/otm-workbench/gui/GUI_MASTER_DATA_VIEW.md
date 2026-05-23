# GUI Master Data View

**Status:** MVP workflow done; first preview, Coordinate Quality, and Load Plan handoff slices done; module-complete follow-ups remain
**Linear:** OTM-114, OTM-117, OTM-118, OTM-91
**QA Linear:** OTM-119
**Scope:** `/master-data` Data Factory staged workflow.

## Objective

Data Factory now supports the first backend-backed Master Data workflow instead
of only inspecting templates.

Delivered story:

```text
template -> author -> workbook -> upload -> validate -> map -> output preview -> csv preview/export -> load-plan package -> cutover checklist -> readiness -> quality
```

## Primary Pattern

```text
staged workflow + object detail
```

The route renders one active stage at a time:

```text
Templates
Author
Workbook
Upload
Validate
Map
Output
Quality
```

The side panel remains focused on selected template metadata and active batch
facts. The frontend does not infer template validity, relationship validity,
mapping readiness, output readiness, CSV readiness, or export readiness.

## Backend Contracts

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
GET  /api/v1/modules/master-data/batches/{batch_id}/output-records
GET  /api/v1/modules/master-data/batches/{batch_id}/csv-files
GET  /api/v1/modules/master-data/batches/{batch_id}/artifacts
GET  /api/v1/modules/master-data/batches/{batch_id}/artifacts/{artifact_id}/download
POST /api/v1/modules/load-plan/packages/from-master-data/{batch_id}
POST /api/v1/modules/load-plan/cutover-checklists/from-package/{package_id}
POST /api/v1/modules/load-plan/cutover-checklists/{checklist_id}/readiness
POST /api/v1/modules/master-data/coordinate-quality/validate
GET  /api/v1/modules/master-data/coordinate-quality/batches
POST /api/v1/modules/master-data/coordinate-quality/batches
GET  /api/v1/modules/master-data/coordinate-quality/batches/{batch_id}/results
POST /api/v1/modules/master-data/coordinate-quality/batches/{batch_id}/export
```

## Out Of Scope

```text
- free-form template authoring from arbitrary N OTM tables
- browser spreadsheet editor
- direct OTM import
- operational batch history analytics beyond list filtering and pagination
- Coordinate Quality advanced map diagnostics and external geocoder setup
```

Batch workflow state is recoverable from backend batch list/detail endpoints.
Generated CSV ZIP artifacts are listed by batch and downloaded through a
batch-scoped guarded URL.

The OTM-117 first slice adds a backend-backed authoring stage using a synthetic
Location template preset. It proves draft creation, definition validation,
publish, and next-version creation through backend contracts. The module is not
yet complete because arbitrary table/field picking and destructive/out-of-order
browser QA remain open.

The second OTM-117 slice connects the authoring stage to Catalog table column
contracts. The user can include/exclude Data Dictionary-backed target columns
before creating the draft.

The third OTM-117 slice connects authoring to Catalog macro-object contracts.
The UI started with the `LOCATION` macro object, then expanded to allow the
author to choose the Catalog macro-object, select its tables, and pick columns
per selected table before creating the backend-owned draft.

The fourth OTM-117 slice adds the first mapping editor controls inside the
Author stage. Selected table columns now expose backend-bound controls for a
friendly upload label, `USER_FIELD`, `FIXED_VALUE`, and `DEFAULT_VALUE` source
types, plus fixed/default values where applicable. The draft request persists
those choices in the backend-owned template definition instead of keeping them
as frontend-only state.

The fifth OTM-117 slice adds the first relationship-rule authoring control for
the `LOCATION` macro object. When `LOCATION_ADDRESS` and its `LOCATION_GID`
column are selected, the user can require the `LOCATION` parent relationship;
the draft then persists a backend-compatible rule using `parent_sheet_code`,
`parent_field_key`, `child_sheet_code`, `child_field_key`, and severity.

The sixth OTM-117 slice starts destructive/out-of-order QA on the Author stage.
If the user enables `LOCATION_ADDRESS`, selects child columns, enables the
relationship rule, then removes `LOCATION_ADDRESS`, dependent child columns,
mapping configuration, and relationship-rule state are cleared before the table
can be re-added. This prevents stale UI state from generating hidden mappings
or relationship rules in the backend draft.

The seventh OTM-117 slice expands browser functional QA for Master Data. The
`qa:functional:master-data:browser` script now validates the Author stage first:
it creates a unique synthetic Location draft, exercises the child-table reset
path, edits a friendly label and default value, enables the relationship rule,
validates the definition, and publishes it before continuing through the
workbook, upload, relationship validation, mapping, output, CSV, export, and
return-state journey.

The eighth OTM-117 slice adds explicit recovery of an existing backend-owned
template definition into the Author stage. When a selected template carries a
`master-data-template-definition/v2` definition, the user can load it into the
authoring controls; the UI reconstructs template code/name, selected target
tables, selected columns, friendly labels, source types, fixed/default values,
and the initial `LOCATION -> LOCATION_ADDRESS` relationship rule from backend
state.

The ninth OTM-117 slice removes the hardcoded Author preview. The mapping
preview now derives its target-table story, user-field count, OTM mapping count,
relationship-rule count, and documentation reference source from the same
backend draft payload used by create/update actions. This keeps the user-facing
summary aligned with the backend-owned definition before the draft is saved.

The tenth OTM-117 slice removes the last hardcoded Catalog table picker from
the Author stage. Macro-object selection now comes from
`GET /api/v1/catalog/macro-objects`, target tables from
`GET /api/v1/catalog/macro-objects/{macro_object_code}/tables`, and columns are
loaded per selected table through `GET /api/v1/catalog/tables/{table}/columns`.
The draft payload persists the selected `catalog_macro_object_code` and uses it
as the Data Dictionary documentation scope.

The first OTM-118 slice adds durable batch and artifact recovery. The backend
now exposes client-safe batch list/detail payloads, batch-scoped artifact
listing, and guarded artifact download with source-module, evidence ownership,
hash, and audit checks. The frontend Output stage renders the backend batch
list and export artifacts, then downloads through the module-scoped guarded URL
instead of relying on session-only `artifact_id` state.

The first OTM-119 hardening slice adds negative artifact availability coverage.
Batch artifact listing now returns `availability_status` and omits
`download_url` when the client-safe evidence record points to a missing file.
This lets the UI keep the export history visible without offering a download
action that is known to fail.

The second OTM-119 hardening slice makes CSV generation resilient to a
double-click or retry after success. Repeating `build-csv` on a `CSV_BUILT`
batch returns the persisted CSV files without duplicating records or moving the
batch backward in the lifecycle.

The third OTM-119 hardening slice applies the same retry contract to CSV
package export. Repeating `export-csv-package` on an `EXPORTED` batch returns
the existing client-safe artifact, manifest, and evidence IDs instead of
creating duplicate packages or returning a lifecycle conflict.

The fourth OTM-119 hardening slice covers invalid upload recovery in the UI.
Backend `ApiError.details.error` is now surfaced in Data Factory feedback, so a
failed workbook upload can explain the specific sheet/header issue and the user
can replace the file and upload successfully without leaving the stage.

The fifth OTM-119 hardening slice expands browser QA route recovery. After
exporting a package, the script leaves Data Factory, returns, opens the Output
stage, and verifies durable backend-owned batch and artifact rows are still
visible.

The first OTM-91 GUI slice places Coordinate Quality inside Data Factory as the
`Quality` stage. The frontend submits synthetic Location records and optional
fake provider candidates to the backend preview endpoint, creates a persisted
quality batch, inspects result rows and recent batches, exports the correction
package, and recovers the recent batch after leaving and returning to the route.
The UI does not duplicate geospatial or OTM Location rules; it orchestrates the
backend-owned Coordinate Quality contracts.

The first Load Plan handoff slice adds guarded package registration from the
Output stage. After a Master Data CSV package is exported, the user can register
the active batch through `POST /api/v1/modules/load-plan/packages/from-master-data/{batch_id}`.
The backend owns eligibility, idempotency, generated package evidence, audit,
domain event, and load sequence; the UI only displays the returned package id,
type, macro object, evidence id, status, and step count.

The second Load Plan handoff slice adds cutover checklist creation from the
registered package. The Output stage calls
`POST /api/v1/modules/load-plan/cutover-checklists/from-package/{package_id}`
and displays the backend checklist id, status, template code, package type,
evidence id, and item count. Checklist item editing remains in Load Plan.

The third Load Plan handoff slice lets Data Factory generate checklist readiness
from the created checklist. The Output stage calls
`POST /api/v1/modules/load-plan/cutover-checklists/{checklist_id}/readiness`
and renders the backend status, ready/review result, blocker count, item count,
evidence id, and backend-returned readiness blockers. Data Factory does not
decide readiness or edit item evidence.

The first backend-owned preview slice adds read-only output and CSV previews to
the Output stage. `GET /output-records` returns generated OTM target-table
payloads, and `GET /csv-files` returns generated CSV file metadata plus a short
preview. The UI does not edit workbook cells or CSV content; editing remains
future scope until a backend-owned mutation contract exists.

The first batch-history slice adds backend-owned filtering and pagination to
`GET /api/v1/modules/master-data/batches`. The Output stage can filter durable
batches by template and lifecycle status, adjust page size, and page through
results without holding a frontend-only history list.

The second batch-history slice expands that backend-owned filter contract with
file-name contains and minimum row-count filters. The Output stage sends those
filters through the same batch list endpoint, so operators can narrow uploaded
workbooks without relying on frontend-only filtering.

The third batch-history slice adds `GET
/api/v1/modules/master-data/batches/summary`. The Output stage renders
backend-owned metrics for the current batch filters: matching batch count,
matching row count, issue count, and status count.
The summary contract intentionally ignores pagination; `page` and `page_size`
belong to the durable batch list only, while summary metrics cover the full
filtered result set.

Master Data batch upload, list, and detail responses now expose backend-owned
`available_actions` for the staged workflow: relationship validation, mapping,
output build, CSV build, package export, and Load Plan registration. The UI
reads those disabled states instead of inferring action eligibility only from
local status checks, and disabled reasons are passed through to button titles.

Master Data template responses also expose backend-owned `available_actions` for
definition validation, template publish, workbook generation, and version
creation. The Author and Workbook stages read those states with frontend
fallbacks for older payloads.

The selected object panel now surfaces backend action guidance for the selected
template and active batch. Each row shows the action scope, whether it is ready
or blocked, and the backend disabled reason when blocked. This makes the real
next step visible without forcing users to infer readiness from disabled buttons
alone.

Master Data `available_actions` now also expose backend-owned `recommended`
metadata. The backend marks the next action that advances the template or batch
workflow, while leaving repeatable/idempotent actions available without making
the UI infer priority from local lifecycle rules.

The Output stage now includes a reset control for durable batch-history filters.
It clears template, status, file-name, minimum-row, page-size, and page state so
operators can recover quickly from over-filtered or stale history views during
QA and repeated upload/export cycles.

Durable batch-history rows can now be inspected directly. Selecting a historical
batch fetches its backend detail, makes it the active batch, refreshes the
selected-object action guidance, and loads that batch's output/artifact surfaces.
This lets QA and cutover operators return to a previous upload/export cycle
without re-running the whole workflow.

When a historical batch is active, the Output stage also exposes a recovery
control that returns the workspace to the latest batch matching the current
filters. This keeps historical inspection reversible without forcing route
navigation or filter resets.

Resetting batch-history filters also clears any manual historical-batch
inspection and returns the active workspace to the latest matching batch. This
prevents a reset from leaving the user in a stale historical context.

The durable batch-history list labels the selected row as the active batch. This
keeps the inspected batch visible in the list itself instead of relying only on
the selected-object side panel.

The first OTM-115 completion slice closes explicit date-column CSV parity
coverage. A synthetic dynamic Item template maps `ITEM.EFFECTIVE_DATE`; generated
CSV and exported ZIP content now have regression coverage proving the OTM CSV
shape remains table line, header line, `exec alter session set nls_date_format =
'YYYY-MM-DD HH24:MI:SS'`, then data rows.

OTM-119 closes the current Master Data MVP workflow hardening pass, and OTM-91
now has its first GUI workflow slice. The module is not marked `Module
complete` because direct OTM import, richer workbook/spreadsheet editing,
advanced Coordinate Quality map diagnostics, deeper Load Plan export/handoff
flows, deeper batch-history analytics beyond current-filter metrics, and
broader negative/out-of-order QA are tracked as follow-up scope.

## Validation

```text
cd frontend
npm run test -- AppFunctionalMasterData.test.tsx
npm run test -- AppFunctionalCoordinateQuality.test.tsx
npm run lint
npm run build
npm run qa:functional:master-data:browser
npm run qa:functional:coordinate-quality:browser
```

Focused OTM-119 backend QA:

```text
python -m pytest tests\test_master_data_templates.py::test_master_data_batch_artifacts_marks_missing_file_unavailable -q
python -m pytest tests\test_master_data_templates.py::test_master_data_batch_build_csv_is_idempotent_for_double_click -q
python -m pytest tests\test_master_data_templates.py::test_master_data_batch_export_csv_package_is_idempotent_for_retry -q
npm run test -- AppFunctionalMasterData.test.tsx -t "shows workbook upload details"
```

Focused OTM-115 backend QA:

```text
python -m pytest tests/test_master_data_templates.py::test_master_data_dynamic_template_date_column_csv_includes_alter_session -q
```

For isolated local QA against a non-default backend port, the Vite development
proxy can be pointed at another backend with `VITE_DEV_PROXY_TARGET`, for
example `http://127.0.0.1:8032`.
