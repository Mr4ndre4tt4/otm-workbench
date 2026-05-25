# GUI Master Data Completion Review OTM-115

**Status:** completed for OTM-115 acceptance  
**Date:** 2026-05-25  
**Branch:** `codex/master-data-hardening-next`  
**Linear:** `OTM-115`

## Purpose

Record the final evidence that Master Data / Data Factory satisfies the
OTM-115 completion acceptance for the current MVP0 scope.

This review does not make future scope disappear. It closes the original
completion gap defined in OTM-115: template discovery, workbook download/upload,
OTM CSV/ZIP parity, UI-driven template authoring, dynamic mappings, durable
state, and positive/negative/out-of-order QA with synthetic data.

## Accepted User Stories

```text
1. Select a Data Dictionary-backed Master Data template.
2. Build and download a workbook template artifact.
3. Fill data through the backend-owned workbook editor or workbook upload path.
4. Validate relationships before mapping when the template defines them.
5. Map user-facing workbook fields to OTM target fields.
6. Build output records and preview generated OTM target-table payloads.
7. Build OTM-shaped CSV files and preview generated CSV content.
8. Export a CSV ZIP package with manifest/evidence/artifact metadata.
9. Register the exported package with Load Plan and generate checklist readiness.
10. Author a new template from Catalog/Data Dictionary-backed macro objects,
    tables, fields, friendly labels, fixed/default mappings, one-to-many
    mappings, relationship rules, publish it, and create a next version.
11. Use backend-owned scenario packs for operational Location and Item Packaging
    stories without exposing client data.
12. Leave and return to the route while recovering durable batch/artifact state
    from backend contracts.
```

## Backend Contract Evidence

The accepted journey uses backend-owned contracts for:

```text
templates list/detail
scenario packs
dynamic template draft/create/update/validate/publish/version
workbook artifact build/download
workbook editor contract/validate/batch creation
workbook upload
relationship validation
mapping
output record preview
CSV file build and preview
CSV ZIP export
batch list/detail/summary
batch artifact list/download
guarded direct OTM import readiness/refusal
Load Plan package registration
cutover checklist creation and readiness
```

The frontend does not infer template validity, OTM target validity,
relationship readiness, batch lifecycle, export eligibility, artifact
availability, direct import eligibility, or cutover readiness.

## Artifact Parity

Master Data generated CSV output is covered against the project OTM CSV rule:

```text
line 1: table name
line 2: target OTM columns
line 3: exec alter session set nls_date_format = 'YYYY-MM-DD HH24:MI:SS'
        when a Data Dictionary DATE column is present
next lines: data rows
```

The same shape is verified inside exported ZIP packages. Generated artifacts
are client-safe, hash-backed, batch-scoped, and downloaded through backend
URLs without exposing local filesystem paths.

## Template Authoring Evidence

The Author stage supports:

```text
Catalog macro-object selection
Catalog/Data Dictionary table and column selection
friendly workbook labels
USER_FIELD mappings
FIXED_VALUE mappings
DEFAULT_VALUE mappings
one user field feeding multiple OTM target columns
relationship rules for parent/child table dependencies
backend definition validation
publish and next-version lifecycle
existing definition recovery into the UI
scenario pack application from backend-owned payloads
authoring reset and selected-template switch recovery
```

## Scenario Coverage

Two synthetic functional scenario packs are accepted as the MVP0 realistic
scenario baseline:

```text
Operational Location:
LOCATION, LOCATION_ADDRESS, LOCATION_CAPACITY,
LOCATION_ACTIVITY_TIME_DEF, LOCATION_LOAD_UNLOAD_POINT,
EQUIPMENT_GROUP_PROFILE, EQUIPMENT_GROUP_PROFILE_D

Item Packaging:
ITEM, SHIP_UNIT_SPEC, PACKAGED_ITEM, TI_HI
```

Both are Data Dictionary-backed and documented in:

```text
docs/otm-workbench/modules/master_data_functional_scenario_qa.md
```

## Negative And Out-Of-Order Evidence

Covered behaviors include:

```text
invalid target table/column validation
missing documentation refs
draft runtime rejection before publish
mapping blocked until relationship validation when rules exist
orphan relationship detection
required workbook field validation
bad workbook upload details surfaced in UI
missing artifact file listed as unavailable without download_url
build-csv retry/double-click idempotency
export-csv-package retry/double-click idempotency
Load Plan registration idempotency
selected template switch clears stale transient state
authoring child-table removal clears dependent mappings/rules
batch-history filter reset recovery
historical batch inspection and return to latest matching batch
route leave/return durable state recovery
guarded direct OTM import readiness and submit refusal
```

## Client Data Safety

The accepted tests and docs use synthetic data only. The workflow does not
display OTM credentials, endpoint tokens, local paths, real client identifiers,
or raw sensitive payloads. Direct OTM import remains guarded and disabled until
a future governed connection/capability design is explicitly implemented.

## Future Scope

The following items are non-blocking enhancements beyond OTM-115 acceptance:

```text
advanced Coordinate Quality map diagnostics
real governed direct OTM submission
deeper spreadsheet editing/audit experience if operationally needed
advanced batch-history analytics beyond current filtered metrics
larger scenario library for additional Master Data families
```

These should be tracked as new issues when prioritized, not as residual
blocking gaps for OTM-115.

