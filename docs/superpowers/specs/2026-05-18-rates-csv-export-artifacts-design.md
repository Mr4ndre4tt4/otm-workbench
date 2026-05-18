# Rates CSV Export Artifacts Design

## Context

The Rates module now has two backend foundations:

- Rates Reference Catalog: reference objects, policies, Data Dictionary metadata,
  and technical CSV preview.
- Rates Batch Contract: persisted batches, scenario templates, submitted OTM
  table rows, validation issues, and batch-level CSV previews.

The next backend-first slice is to turn validated batch data into a durable CSV
export package that uses the existing platform artifact, manifest, evidence, and
audit concepts. This is still not real OTM upload, not CSVUTIL, not Load Plan,
not XML, and not UI.

Inputs used:

- `docs/superpowers/specs/2026-05-18-rates-batch-contract-design.md`
- `docs/otm-workbench/foundation/modelo_artifacts_evidencias_manifestos_otm_workbench.md`
- `docs/otm-workbench/foundation/modelo_dados_contratos_api_otm_workbench.md`
- `src/otm_workbench/platform/routes.py`
- `src/otm_workbench/models.py`
- local OTM Data Dictionary under `OTM_RESOURCES/DATA_DICT26B`

## Goal

Add backend support for generating a durable, hash-tracked Rates CSV export
package from a validated Rates batch, with a manifest and client-safe evidence
record.

The package should be useful for review and later Load Plan integration, but it
must not claim that the data has been loaded into OTM.

## Scope

Included:

- Endpoint to export a validated Rates batch as CSV files.
- One generated `.csv` file per persisted batch table.
- A ZIP package containing the CSV files and a JSON manifest.
- Artifact metadata for the ZIP package using the platform `Artifact` model.
- Manifest metadata using the platform `Manifest` model.
- Client-safe evidence using the platform `Evidence` model.
- Audit log entry for export generation.
- Batch status transition to `EXPORTED`.
- Batch `exported_at` timestamp.
- A package response with `artifact_id`, `manifest_id`, `evidence_id`,
  `sha256`, `size_bytes`, and included table names.

Excluded:

- UI.
- Real OTM upload.
- CSVUTIL CTL/CL generation.
- Load Plan package registration.
- XML export.
- Excel workbook export.
- Download endpoint changes.
- Approval workflow beyond using the existing validated batch state.

## Preconditions

The first implementation should allow export only when the batch is already
valid enough for generated CSV package review:

- `RateBatch.status` must be `VALIDATED` or `EXPORT_PREVIEWED`.
- The latest persisted issues must not contain `ERROR`.
- The batch must contain at least one `RateBatchTable` with at least one row.
- Each table and column must still pass Data Dictionary validation during export.

If the batch is `DRAFT` with errors, export returns a 400 response with a clear
message. The export endpoint may call the existing validation service before
exporting to avoid stale issue state.

## Export Package Shape

Package path should be under the configured artifact root:

```text
{artifact_root}/rates/{batch_id}/exports/{timestamp}/rates_batch_{batch_id}.zip
```

ZIP contents:

```text
manifest.json
csv/
  001_RATE_OFFERING.csv
  002_RATE_UNIT_BREAK_PROFILE.csv
  003_RATE_UNIT_BREAK.csv
  004_X_LANE.csv
  ...
```

Only tables present in the batch are included. File numbering follows the
canonical Rates load sequence, not insertion order.

Each CSV file must use the existing OTM table format:

```text
TABLE_NAME
COLUMN_1,COLUMN_2
exec alter session set nls_date_format = 'YYYY-MM-DD HH24:MI:SS'
value_1,2026-01-01 00:00:00
```

The date directive is included only for CSV files whose selected columns include
at least one Data Dictionary DATE column.

## Manifest Contract

`manifest.json` inside the ZIP and `Manifest.manifest_json` in DB should contain
the same client-safe summary:

```json
{
  "schema_version": "rates-csv-export-manifest/v1",
  "manifest_type": "rates_csv_export",
  "source_module": "rates",
  "source_entity_type": "rate_batch",
  "source_entity_id": "batch_id",
  "batch": {
    "id": "batch_id",
    "scenario_code": "RATE_GEO_ONLY",
    "status": "EXPORTED",
    "domain_name": "OTM1"
  },
  "files": [
    {
      "table_name": "RATE_GEO",
      "file_name": "004_RATE_GEO.csv",
      "row_count": 1,
      "sha256": "file hash",
      "size_bytes": 123
    }
  ],
  "validation_summary": {
    "errors": 0,
    "warnings": 2,
    "infos": 0
  },
  "generated_at": "ISO timestamp",
  "generated_by": "user email"
}
```

The manifest must not include raw row values. It may include file names, table
names, counts, hashes, status, and issue counts.

## Artifact Contract

Create one `Artifact` row for the ZIP package:

```text
source_module = "rates"
artifact_type = "rates_csv_zip"
file_path = absolute or workspace-relative ZIP path
file_name = rates_batch_{batch_id}.zip
content_type = application/zip
sensitivity_level = internal
sha256 = computed ZIP hash
size_bytes = ZIP size
```

The current platform artifact model does not yet include all future fields from
the foundation docs, such as `source_entity_type`, `source_entity_id`, and
`created_by`. This slice should not expand the platform model unless required.
Those values belong in the manifest and evidence summaries for now.

## Evidence Contract

Create one `Evidence` row:

```text
source_module = "rates"
evidence_type = "rates_csv_export"
artifact_id = generated ZIP artifact id
manifest_id = generated manifest id
client_safe = true
sensitivity_level = client_safe
status = CREATED
```

`summary_json` must be client-safe:

```json
{
  "source_entity_type": "rate_batch",
  "source_entity_id": "batch_id",
  "scenario_code": "RATE_GEO_ONLY",
  "domain_name": "OTM1",
  "table_count": 4,
  "row_count": 12,
  "validation_summary": {
    "errors": 0,
    "warnings": 1,
    "infos": 0
  },
  "artifact_type": "rates_csv_zip"
}
```

Do not store CSV text, raw row payloads, charges, lane values, or full GIDs in
evidence. Synthetic test GIDs may appear only in tests and generated local files.

## API Contract

Add:

```text
POST /api/v1/modules/rates/batches/{batch_id}/export-csv
GET  /api/v1/modules/rates/batches/{batch_id}/artifacts
GET  /api/v1/modules/rates/batches/{batch_id}/evidence
```

`POST export-csv` response:

```json
{
  "batch_id": "batch_id",
  "status": "EXPORTED",
  "artifact_id": "artifact_id",
  "manifest_id": "manifest_id",
  "evidence_id": "evidence_id",
  "file_name": "rates_batch_batch_id.zip",
  "sha256": "zip hash",
  "size_bytes": 1234,
  "tables": ["X_LANE", "RATE_GEO"]
}
```

`GET artifacts` returns artifacts related to the batch by reading
`Manifest.manifest_json` or `Evidence.summary_json` source entity fields.

`GET evidence` returns evidence related to the batch, never raw CSV content.

## Audit

Create one `AuditLog` row for export:

```text
action = "rates.batch.export_csv"
target_type = "rate_batch"
target_id = batch_id
metadata_json = {
  "artifact_id": "...",
  "manifest_id": "...",
  "evidence_id": "...",
  "table_count": 4
}
```

## Validation And Data Dictionary Rules

Export must reuse the existing Data Dictionary-backed CSV builder. It must not
serialize arbitrary JSON into CSV without table/column validation.

The special technical rules from the previous slice remain active:

- `RATE_GEO.RATE_GEO_SEQ` is omitted.
- `RATE_GEO_COST_GROUP.RATE_GEO_COST_GROUP_SEQ` defaults to `1`.
- `RATE_GEO_COST.RATE_GEO_COST_SEQ` is generated per cost group when missing.
- `RATE_GEO_COST.CHARGE_AMOUNT_BASE` is blank when present.
- DATE columns trigger the OTM date format directive.

## Testing Strategy

Minimum tests:

- export rejects a batch that has not been validated;
- export rejects a batch with persisted `ERROR` issues;
- export creates a ZIP artifact for a validated batch;
- ZIP contains `manifest.json` and one CSV per batch table;
- CSV files keep table name on line 1 and columns on line 2;
- CSV files preserve date directive behavior for DATE columns;
- artifact row stores `rates_csv_zip`, hash, size, and path;
- manifest row stores client-safe package metadata without raw row values;
- evidence row is client-safe and references artifact and manifest;
- batch moves to `EXPORTED` and gets `exported_at`;
- audit log records `rates.batch.export_csv`;
- artifacts/evidence endpoints return only records for that batch.

## Risks

Export can be mistaken for OTM load readiness. Mitigation: name the artifact
`rates_csv_zip`, keep status `EXPORTED`, and avoid Load Plan or CSVUTIL language
in this slice.

Evidence can leak raw tariff data. Mitigation: store only counts, hashes,
statuses, artifact references, and manifest references in evidence.

Package content can drift from preview behavior. Mitigation: reuse the same
Data Dictionary-backed CSV builder for preview and export.

## Decisions

- Start with ZIP package artifact only, not individual Artifact rows per CSV.
- Store per-file details inside manifest JSON.
- Keep `sensitivity_level = internal` for ZIP artifacts.
- Keep evidence client-safe and free of raw rows.
- Do not expand platform artifact schema in this slice.
- Do not create Load Plan package records yet.

## Next Steps

1. Write a TDD implementation plan.
2. Implement export service under `modules/rates`.
3. Add routes for `export-csv`, `artifacts`, and `evidence`.
4. Add tests for ZIP contents, manifest, evidence, and audit.
5. Run tests, Alembic, and Ruff.

## Last Updated

2026-05-18
