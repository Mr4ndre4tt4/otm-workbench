# GUI Master Data View

**Status:** authoring and durable artifact slice delivered; completion QA hardening remains
**Linear:** OTM-114, OTM-117, OTM-118
**Scope:** `/master-data` Data Factory staged workflow.

## Objective

Data Factory now supports the first backend-backed Master Data workflow instead
of only inspecting templates.

Delivered story:

```text
template -> author -> workbook -> upload -> validate -> map -> output/export
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
GET  /api/v1/modules/master-data/batches/{batch_id}/artifacts
GET  /api/v1/modules/master-data/batches/{batch_id}/artifacts/{artifact_id}/download
```

## Out Of Scope

```text
- Coordinate Quality GUI
- free-form template authoring from arbitrary N OTM tables
- browser spreadsheet editor
- Load Plan registration from Data Factory
- direct OTM import
- advanced batch history filters/pagination
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

## Validation

```text
cd frontend
npm run test -- AppFunctionalMasterData.test.tsx
npm run lint
npm run build
npm run qa:functional:master-data:browser
```

For isolated local QA against a non-default backend port, the Vite development
proxy can be pointed at another backend with `VITE_DEV_PROXY_TARGET`, for
example `http://127.0.0.1:8032`.
