# Load Plan ZIP Analysis Design

## Context

Load Plan already registers approved Rates CSV exports as `LoadPlanPackage`
records and can generate internal CSVUTIL CTL/CL control artifacts for those
packages. The roadmap item after CSVUTIL Builder is ZIP Analysis: a backend
history of what is inside a package before setup review, load sequence changes,
or cutover readiness decisions.

This slice stays passive. It inspects package artifacts, records client-safe
metadata and findings, and keeps raw row values out of persisted evidence.

## Goal

Add backend/API support for analyzing a registered Load Plan package ZIP,
persisting analysis history, manifest, evidence, audit, and domain-event
metadata without executing CSVUTIL or connecting to OTM.

## Scope

Included:

- New `LoadPlanZipAnalysis` persistence model.
- Alembic migration for `load_plan_zip_analyses`.
- `POST /api/v1/modules/load-plan/zip-analysis`.
- `GET /api/v1/modules/load-plan/zip-analysis`.
- `GET /api/v1/modules/load-plan/zip-analysis/{analysis_id}`.
- ZIP inspection using the package source artifact.
- Manifest inspection when `manifest.json` is present inside the ZIP.
- CSV structure checks for package files under `csv/`.
- Data Dictionary checks for table existence and known columns.
- Client-safe findings with severity, code, message, table, and file metadata.
- Manifest row with `manifest_type="zip_analysis"`.
- Evidence row with `evidence_type="load_plan_zip_analysis"`.
- Audit log action `load_plan.zip_analysis.run`.
- Domain event `load_plan.zip_analysis.completed`.

Excluded:

- Running CSVUTIL.
- Connecting to OTM.
- Uploading or validating records in OTM.
- Rewriting ZIP or CSV content.
- Creating setup review queue items.
- Making review decisions.
- Producing cutover readiness or blockers.
- UI.

## Data Dictionary And CSV Rules

The analyzer must consult
`OTM_RESOURCES/DATA_DICT26B/data_dictionary/json/data_dict` for table metadata.
This is used to confirm that a CSV table exists in the OTM dictionary and that
header columns are known for that table. It should not infer OTM semantics from
filename patterns alone.

The expected OTM CSV format remains:

```text
table name line
column header line
exec alter session set nls_date_format = 'YYYY-MM-DD HH24:MI:SS'
value lines
```

The `exec alter session...` line is required only when the CSV header includes
one or more Data Dictionary columns with `DATE` type. If no date columns are in
the header, value lines may begin immediately after the column header.

The analyzer should read CSV structure and counts, but should not persist row
values. It can persist table names, column names, row counts, filenames, hashes,
sizes, and finding messages.

## Model Contract

Add `LoadPlanZipAnalysis`:

```text
id
project_id
environment_id
profile_id
package_id
status
source_artifact_id
source_manifest_id
manifest_id
evidence_id
summary_json
findings_json
created_by
analyzed_at
created_at
updated_at
```

Indexes should follow the existing Load Plan style:

- `project_id`
- `environment_id`
- `profile_id`
- `package_id`
- `status`
- `source_artifact_id`
- `source_manifest_id`
- `manifest_id`
- `evidence_id`

Initial statuses:

- `ANALYZED`: ZIP was opened and analyzed.
- `FAILED`: reserved for future async/job usage; this synchronous MVP should
  generally return a 400 for non-analyzable packages instead of persisting
  partial failed runs.

## Analysis Contract

The service accepts a registered package and inspects the ZIP referenced by
`LoadPlanPackage.artifact_id`.

Validation before analysis:

- Package exists.
- Package status is `REGISTERED`.
- Package has `artifact_id`, `manifest_id`, and non-empty load sequence.
- Source artifact exists.
- Source artifact path exists on disk.
- Source artifact is a readable ZIP.

Inspection:

- List ZIP members and identify `manifest.json`.
- Identify files matching `csv/*.csv`.
- For each CSV:
  - calculate file SHA-256 and uncompressed size;
  - read first non-empty structural lines;
  - treat line 1 as table name;
  - treat line 2 as comma-separated column header;
  - detect optional `exec alter session set nls_date_format = 'YYYY-MM-DD HH24:MI:SS'`;
  - count data rows after the structural lines;
  - compare the table name to the package load sequence;
  - confirm the table exists in the Data Dictionary;
  - confirm every header column exists in the Data Dictionary table;
  - identify whether date columns are present and whether the alter-session
    line is present when needed.

Findings are deterministic dictionaries:

```text
severity: INFO | WARNING | ERROR
code: stable machine-readable code
message: client-safe description
table_name: optional table name
file_name: optional ZIP member name
details: client-safe structured metadata
```

Suggested initial finding codes:

- `ZIP_MANIFEST_MISSING`
- `ZIP_CSV_MISSING`
- `CSV_TABLE_LINE_MISSING`
- `CSV_HEADER_LINE_MISSING`
- `CSV_TABLE_NOT_IN_LOAD_SEQUENCE`
- `CSV_TABLE_NOT_IN_DATA_DICTIONARY`
- `CSV_UNKNOWN_COLUMN`
- `CSV_DATE_ALTER_SESSION_MISSING`
- `CSV_ROW_COUNT_MISMATCH`

The package can still be `ANALYZED` when warnings or errors exist. Those
findings inform future setup review and readiness slices, but this slice does
not decide whether a package can move forward.

## Manifest And Evidence

Create a `Manifest` row:

```text
schema_version: load-plan-zip-analysis-manifest/v1
manifest_type: zip_analysis
source_module: load_plan
source_entity_type: load_plan_package
source_entity_id: package id
package: client-safe package metadata
source_artifact: artifact id, file name, sha256, size
files: CSV file metadata, table names, row counts, hashes
summary: counts and finding totals
findings: client-safe finding list
analyzed_at
analyzed_by
```

Create an `Evidence` row:

```text
source_module: load_plan
evidence_type: load_plan_zip_analysis
client_safe: true
sensitivity_level: client_safe
summary_json: counts, ids, status, finding totals
artifact_id: source package artifact id
manifest_id: zip analysis manifest id
```

Evidence and manifest must not include raw row values.

## API Contract

`POST /api/v1/modules/load-plan/zip-analysis`

Request:

```json
{
  "package_id": "..."
}
```

Response:

```json
{
  "id": "...",
  "project_id": "...",
  "environment_id": "...",
  "profile_id": "...",
  "package_id": "...",
  "status": "ANALYZED",
  "source_artifact_id": "...",
  "source_manifest_id": "...",
  "manifest_id": "...",
  "evidence_id": "...",
  "summary": {
    "file_count": 2,
    "csv_file_count": 1,
    "table_count": 1,
    "row_count": 1,
    "finding_count": 0,
    "error_count": 0,
    "warning_count": 0
  },
  "findings": [],
  "created_by": "synthetic@example.com",
  "analyzed_at": "..."
}
```

`GET /api/v1/modules/load-plan/zip-analysis`

Returns `PageResponse` ordered newest first.

`GET /api/v1/modules/load-plan/zip-analysis/{analysis_id}`

Returns one analysis or 404.

## Errors

Use the existing FastAPI route style:

- `404` when package or analysis id does not exist.
- `400` when the package is not registered, has no artifact/manifest/load
  sequence, references a missing artifact, or references a non-ZIP/unreadable
  artifact.

The analyzer should convert zip parsing failures into a client-safe 400 message
such as `Load Plan package artifact must be a readable ZIP.`

## Testing

Add backend tests that build a synthetic Rates batch through the existing
approval, export, package intake, and ZIP analysis flow.

Test coverage:

- Successful ZIP analysis persists `LoadPlanZipAnalysis`, manifest, evidence,
  audit log, and domain event.
- Response includes file/table/row counts and client-safe finding totals.
- Analysis uses Data Dictionary metadata for `ACCESSORIAL_COST`.
- Date-bearing CSV headers require the alter-session line when date columns are
  present.
- Unknown columns produce `CSV_UNKNOWN_COLUMN`.
- Missing source artifact or non-ZIP artifact returns 400.
- List and detail endpoints return serialized analysis contracts.

Tests must use synthetic identifiers only, such as `OTM1`, `PUBLIC`, `DEMO`,
and generated IDs. No real client names or row values should appear in
assertions.

## Security And Privacy

ZIP Analysis can see package files, but persisted outputs must remain
client-safe. Store metadata, hashes, counts, table names, column names, and
finding messages only. Do not copy raw CSV data rows into `summary_json`,
`findings_json`, `Manifest.manifest_json`, `Evidence.summary_json`, audit logs,
or events.

This slice does not introduce new user capabilities yet. It should use the
existing authenticated route dependency and keep capability enforcement aligned
with the current Load Plan endpoints.

## Risks

ZIP Analysis can be mistaken for setup review. Mitigation: produce findings,
not decisions, queue items, approvals, blockers, or readiness.

ZIP Analysis can be mistaken for OTM validation. Mitigation: status
`ANALYZED` means the local package was inspected only. It does not mean OTM
accepted the data.

Data Dictionary lookup can be brittle if table names differ by case. Mitigation:
normalize table names to uppercase for package analysis while reading dictionary
files case-insensitively where practical.

## Implementation Notes

Prefer a focused module `src/otm_workbench/modules/load_plan/zip_analysis.py`.
Keep JSON parsing helpers from `packages.py` reused where they already fit.

Use Python `zipfile` for ZIP inspection and `csv` for header parsing. Avoid
manual comma splitting for the CSV header because quoted column names are valid
CSV syntax even if uncommon in these generated artifacts.

The implementation should not modify the source ZIP or any upstream Rates
artifacts.
