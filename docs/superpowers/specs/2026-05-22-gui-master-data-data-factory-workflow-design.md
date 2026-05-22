# GUI Master Data Data Factory Workflow Design

**Status:** approved for implementation
**Date:** 2026-05-22
**Linear:** OTM-114
**Scope:** first staged GUI workflow slice for `/master-data`.

## Objective

Turn Data Factory from template inspection into a backend-backed staged workflow
that proves one Master Data template can move through workbook, upload,
validation, mapping, output, CSV, and export states without stacking
disconnected panels.

## Product Story

The first story is:

```text
select template -> validate template -> build workbook -> upload synthetic
workbook -> validate relationships -> map canonical records -> build output ->
build CSV -> export package -> leave route -> return with backend-owned state
visible
```

The route remains backend-first. The frontend orchestrates user actions and
renders status, but backend APIs decide validity, readiness, generated artifact
metadata, and blocked/error outcomes.

## Primary Pattern

Use the existing GUI module foundation with:

```text
Primary pattern: staged workflow + object detail
Primary object: Master Data template, then the active uploaded batch
Side panel: selected template and active batch facts
Main panel: one stage visible at a time
```

The stage order is:

```text
Templates -> Workbook -> Upload -> Validate -> Map -> Output
```

`Output` includes build output, build CSV, and export package because those are
closely related finalization steps for the first slice. If this becomes too
dense after implementation, it should be split into `Output` and `Export` in a
follow-up issue rather than adding more panels to the page.

## Backend Contracts

The first slice uses existing backend contracts:

```text
GET  /api/v1/modules/master-data/templates
GET  /api/v1/modules/master-data/templates/{template_code}
POST /api/v1/modules/master-data/templates/{template_code}/validate
POST /api/v1/modules/master-data/templates/{template_code}/build-workbook
POST /api/v1/modules/master-data/templates/{template_code}/batches
POST /api/v1/modules/master-data/batches/{batch_id}/validate-relationships
POST /api/v1/modules/master-data/batches/{batch_id}/map
POST /api/v1/modules/master-data/batches/{batch_id}/build-output
POST /api/v1/modules/master-data/batches/{batch_id}/build-csv
POST /api/v1/modules/master-data/batches/{batch_id}/export-csv-package
```

No new backend endpoint is required for this slice unless the browser QA proves
that route return-state cannot recover batch status without a read endpoint.
If that happens, the smallest acceptable backend addition is a batch detail
read endpoint, not frontend-only durable state.

## UI Behavior

The page keeps the existing top metric grid for template inventory. The main
workspace title changes from `Templates` to `Data Factory workflow`.

The main area renders a workflow step control:

```text
1 Templates
2 Workbook
3 Upload
4 Validate
5 Map
6 Output
```

Only the active stage renders its operational surface.

### Templates

Shows the existing template list. Selecting a template updates the side panel
and all subsequent action endpoints.

### Workbook

Shows template validation and workbook generation actions:

```text
Validate template
Build workbook
Download workbook
```

The first implementation may show generated workbook metadata without download
if no generic artifact download path is available from the response. If
download is wired, it must use guarded backend artifact download logic and not
render local paths.

### Upload

Provides a file input and upload action for the selected template. The upload
must send `multipart/form-data` to the backend. Tests use a synthetic workbook.

After upload, the UI stores the returned batch payload in component state and
shows backend-owned batch status, row counts, and template code.

### Validate

Runs relationship validation for the active batch. The result is rendered as a
backend response, including valid/blocker states. The frontend must not infer
relationship validity from workbook content.

### Map

Runs canonical mapping for the active batch. The UI shows status and summary
from the backend response. Mapping readiness is backend-owned.

### Output

Runs build output, build CSV, and export package in sequence through separate
explicit buttons. Each action updates the visible backend result. Export
metadata must be client-safe and must not expose local artifact paths.

## State Model

Frontend state may hold only ephemeral route state:

```text
selectedTemplateCode
activeStage
templateValidation
workbookArtifact
uploadedBatch
relationshipValidation
mappingResult
outputResult
csvResult
exportResult
operationMessage
operationError
isMutating
selectedUploadFile
```

Durable truth remains backend-owned. If the user leaves the route and returns
within the same authenticated session, the first slice must still show
template state and selected template from backend queries. If batch recovery is
not possible yet, the QA matrix must record that gap and a follow-up read
endpoint issue must be created.

## Testing

Layer 1:

```text
frontend/src/app/AppFunctionalMasterData.test.tsx
```

The test mocks backend contracts and asserts:

```text
- staged workflow is visible
- user selects or uses the default template
- template validation POST uses bearer auth
- workbook generation POST uses bearer auth
- file upload uses FormData and bearer auth
- relationship validation, map, build output, build CSV, and export package
  POSTs use bearer auth
- backend response statuses are rendered
- user leaves and returns to `/master-data`
- template state is still visible from backend-owned queries
```

Layer 2:

```text
npm run qa:functional:master-data:browser
```

The browser script should use local FastAPI + Vite, login as the demo user,
open Data Factory, generate a synthetic workbook through the backend or create
one in the script, upload it, execute the workflow, leave the route, return,
and assert no console or HTTP failures.

Layer 3:

```text
python -m pytest tests/test_master_data_templates.py -q
```

Backend tests already cover template validation, workbook generation, upload,
relationship validation, mapping, output, CSV, export, evidence, artifacts, and
manifest behavior.

## Documentation

Update:

```text
docs/otm-workbench/gui/GUI_FUNCTIONAL_QA_JOURNEYS.md
docs/otm-workbench/gui/GUI_MODULE_EXPERIENCE_ROADMAP.md
docs/otm-workbench/gui/GUI_MVP1_PLAN.md
```

Create or update a Data Factory view doc if one is missing.

## Out Of Scope

This slice does not implement:

```text
- Coordinate Quality GUI
- advanced workbook editor
- spreadsheet preview/editing in the browser
- template authoring
- batch history across sessions unless supported by existing or minimal backend
  read contracts
- Load Plan registration from the Data Factory page
- direct OTM import
```

## Risks And Follow-Ups

The main risk is batch return-state. The existing backend flow is action-rich
but may not expose a direct batch detail/list endpoint. If browser QA confirms
that limitation, create a follow-up or small backend read endpoint rather than
persisting batch truth in frontend storage.

Another risk is making `Output` too dense. If the output stage feels crowded,
split export into a follow-up staged step.

## Self-Review

Placeholder scan: no placeholders remain.

Scope check: one route, one first Data Factory story, no Coordinate Quality.

Backend ownership check: validation, mapping, readiness, CSV/export, artifacts,
and blockers remain backend-owned.

Ambiguity check: return-state expectation is explicit: template state must
return now; batch return-state requires backend read support or a documented
follow-up.
