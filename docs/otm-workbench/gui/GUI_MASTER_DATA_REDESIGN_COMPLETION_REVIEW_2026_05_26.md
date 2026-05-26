# GUI Master Data Redesign Completion Review

**Status:** verified for current redesign scope  
**Date:** 2026-05-26  
**Scope:** Master Data hub, Data Factory, Template Builder, and Quality Tools
route-family redesign.

## 1. Purpose

Record the evidence that the Master Data redesign moved the module from one
overloaded staged screen into clear route families with route-level details,
backend-owned actions, browser QA screenshots, and direct route recovery.

This review extends, but does not replace, the earlier MVP workflow reviews:

```text
GUI_MASTER_DATA_COMPLETION_REVIEW_OTM115.md
GUI_MASTER_DATA_MVP_WORKFLOW_REVIEW_OTM119.md
```

Those documents close the original backend and artifact workflow acceptance.
This review closes the 2026-05-26 UI redesign acceptance for the current module
slice.

## 2. Route Inventory

Delivered route families:

```text
/master-data
/master-data/factory
/master-data/factory/templates/:templateCode
/master-data/factory/batches/:batchId
/master-data/template-builder
/master-data/template-builder/new
/master-data/template-builder/:templateCode
/master-data/template-builder/:templateCode/edit
/master-data/template-builder/:templateCode/copy
/master-data/template-builder/:templateCode/delete
/master-data/quality
/master-data/quality/lat-lon
/master-data/quality/lat-lon/batches/:batchId
```

Each drill-down, edit, copy, delete/retire, and result route has a visible
return path. Complex actions are no longer hidden inside a shared selected
object side panel.

## 3. Delivered UX Decisions

The redesign now separates the three Master Data jobs:

```text
Data Factory:
  operational template selection, workbook/editor input, batch validation,
  output, CSV package, guarded OTM import readiness, Load Plan handoff.

Template Builder:
  template list/search, detail, create, edit, copy, and guarded retire impact.

Quality Tools:
  Lat/Lon validation, persisted quality batch detail, result inspection, and
  correction package export.
```

The UI keeps the screens dense enough for implementation work while avoiding
the previous mixed workflow strip. Template authoring, batch execution, and
coordinate quality are not presented as one linear process.

## 4. Backend Contract Alignment

The redesign keeps backend ownership for:

```text
template list/detail/search
template available actions and disabled reasons
template draft create/update/validate/publish/version
workbook generation and workbook editor validation
batch create/detail/list/summary
relationship validation, mapping, output, CSV build, package export
guarded OTM import readiness and blocked submit
Load Plan package registration and checklist readiness
Coordinate Quality preview, batch create/detail/results/export
```

The frontend does not infer template validity, OTM table validity, batch
lifecycle readiness, export eligibility, direct import eligibility, Load Plan
readiness, or coordinate-quality result status.

## 5. QA Evidence

Backend and API evidence:

```text
python -m pytest tests/test_master_data_templates.py
python -m pytest tests/test_coordinate_quality_api.py tests/test_coordinate_quality_engine.py
```

Recent result:

```text
70 passed
```

Frontend contract evidence:

```text
npm test -- src/app/App.test.tsx
npm test -- src/app/AppFunctionalMasterData.test.tsx
npm test -- src/app/AppFunctionalCoordinateQuality.test.tsx
npm run qa:functional:master-data
npm run qa:functional:coordinate-quality
```

Recent result:

```text
28 passed across App, Master Data, and Coordinate Quality contract tests
5 passed for qa:functional:master-data
2 passed for qa:functional:coordinate-quality
```

Browser and build evidence:

```text
npm run qa:functional:master-data:browser
npm run qa:functional:coordinate-quality:browser
npm run build
git diff --check
```

Recent result:

```text
master-data browser journey passed
coordinate-quality browser journey passed
production build passed
git diff --check passed with CRLF normalization warnings only
```

Known non-failing warnings from the current harness:

```text
jsdom prints a navigation-not-implemented warning for artifact/download style
interactions that intentionally leave actual document navigation to browser QA.

Vite prints the existing chunk-size warning after build because the current app
bundle is larger than the default 500 kB advisory threshold.
```

## 6. Screenshot Evidence

Current screenshot evidence is stored under `output/gui-qa/master-data/`:

```text
01-master-data-hub.png
02-template-builder-entry.png
02-template-builder-search.png
02-template-builder-detail.png
02-template-builder-copy.png
02-template-builder-copy-created.png
02-template-builder-edit.png
02-template-builder-retire.png
02-template-builder-new.png
03-data-factory-entry.png
04-template-detail-regions-basic.png
05-batch-detail-input.png
06-batch-detail-validated.png
07-batch-detail-csv-package.png
08-batch-detail-load-plan.png
09-quality-tools-hub.png
10-lat-lon-validator.png
11-lat-lon-batch-detail.png
12-lat-lon-export.png
```

The screenshots use synthetic local data only. No real client data, credentials,
local customer paths, or production identifiers are used.

## 7. Happy, Negative, Out-Of-Order, And Recovery Coverage

Covered:

```text
happy operational batch path through workbook editor, validation, output, CSV,
export package, guarded OTM import readiness, and Load Plan handoff

invalid workbook editor input and invalid workbook upload recovery

blocked map-before-relationship-validation state from backend available actions

template switch recovery after workbook/output/export/Load Plan route-session
state exists

Template Builder list search, route-level detail, create, edit, copy, and
guarded retire impact path

copy route navigation into the copied draft edit route

Lat/Lon hub, validator workspace, batch create, route-level detail, export, and
return-state recovery

direct URL recovery for /master-data/quality/lat-lon/batches/:batchId through
the backend batch detail endpoint
```

## 8. Remaining Explicit Follow-Up Scope

The following are not blockers for the redesign completion review:

```text
real governed direct OTM submission
deeper audited spreadsheet editing
advanced Coordinate Quality map diagnostics and external provider governance
dedicated Template Builder retire/delete backend mutation
copy-option granularity in the backend version/copy endpoint
deeper Load Plan export/handoff beyond current package/checklist readiness
larger scenario-pack library for additional Master Data families
```

These should remain separate Linear/GitHub follow-ups when prioritized.

## 9. Completion Decision

The current Master Data redesign slice is complete for the implemented scope.
The final verification commands above were rerun on 2026-05-26 and passed.
Linear comments were added to `OTM-115` and `OTM-146` with this evidence path.
GitHub evidence remains local to the repository/branch because this workspace
does not currently expose a PR target or a local `gh` client.

The next module-planning step can start with `GUI_CATALOG_CORE_ROADMAP_SPEC.md`
because Catalog Core now supplies shared schema, macro-object, and Data
Dictionary inputs used by Master Data, Rates, Integration Mapping, and Order
Release Generator.
