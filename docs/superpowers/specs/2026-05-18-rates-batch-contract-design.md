# Rates Batch Contract Design

## Context

This document defines the next backend-first slice of the Rates module after the
Rates Reference Catalog foundation. The goal is to introduce a technical batch
contract for rate uploads without implementing UI, real OTM integration, XML
export, Load Plan, or client-specific examples.

Inputs used for this design:

- `C:\Users\Enzo Trabalho\Downloads\Instrucoes Rates OTM.md`
- `C:\Users\Enzo Trabalho\Downloads\mvp0_tarifas_reference_catalog.md`
- `OTM_RESOURCES/DATA_DICT26B/data_dictionary/json/data_dict`
- Existing code under `src/otm_workbench/modules/rates`

The local OTM Data Dictionary is mandatory for validating table names, column
names, date columns, foreign-key dependencies, and load sequence behavior.

## Goal

Create the backend, database, and API contract for technical Rates batches so
future screens or scripts can submit tariff rows, validate them, inspect issues,
and generate OTM-compatible CSV previews in the correct table order.

This slice does not create the final tariff workbook. It creates a stable
internal representation that can later be populated from Excel, API calls, or
other import sources.

## Scope

Included:

- Rate batch lifecycle and persistence.
- Rate batch table groups and row payloads.
- Three initial batch scenarios:
  - complete tariff
  - rate geo only
  - accessorial only
- Scenario table requirements: required, optional, and pre-existing.
- Data Dictionary validation for every submitted table and column.
- Sequence validation using the canonical Rates load sequence.
- Technical row issues with `ERROR`, `WARNING`, and `INFO`.
- CSV preview generation per OTM table.
- Date directive handling before values when a selected table has DATE columns.
- Special technical handling for OTM sequence/base columns requested in the
  source instructions.

Excluded:

- UI.
- Final Excel template.
- XML export.
- Real OTM upload or OTM API calls.
- CSVUTIL package generation for Load Plan.
- Client names, client examples, or real customer domains.

## Recommended Approach

Use a compact batch model around three concepts:

1. `RateBatch`: the user-visible unit of work and lifecycle.
2. `RateBatchTable`: one OTM table inside the batch, ordered by the canonical
   sequence.
3. `RateBatchRow`: one JSON row for a given table, preserving submitted values
   while validation produces separate issue records.

This keeps the design backend-only and makes future UI, workbook parsing, and
exporters consumers of the same contract instead of sources of business rules.

Alternative approaches considered:

- Template-only first: smaller, but it would not prove lifecycle, validation,
  or row storage.
- Direct CSV export first: tempting, but risky because it skips the persisted
  batch state needed for review, approval, and evidence later.

## Batch Scenarios

The first implementation should support these scenario codes:

| Code | Purpose |
|---|---|
| `COMPLETE_TARIFF` | Rate offering plus rate geo, accessorial, and cost tables. |
| `RATE_GEO_ONLY` | Rate records and costs when the offering already exists or is out of scope. |
| `ACCESSORIAL_ONLY` | Accessorial costs and relationships without creating a full rate geo package. |

### COMPLETE_TARIFF

Tables in load order:

1. `RATE_OFFERING`
2. `RATE_UNIT_BREAK_PROFILE`
3. `RATE_UNIT_BREAK`
4. `X_LANE`
5. `RATE_GEO`
6. `ACCESSORIAL_CODE`
7. `ACCESSORIAL_COST`
8. `ACCESSORIAL_COST_UNIT_BREAK`
9. `RATE_OFFERING_ACCESSORIAL`
10. `RATE_GEO_ACCESSORIAL`
11. `RATE_GEO_STOPS`
12. `RATE_GEO_COST_GROUP`
13. `RATE_GEO_COST`

Required for the scenario:

- `X_LANE`
- `RATE_GEO`
- `RATE_GEO_COST_GROUP`
- `RATE_GEO_COST`

Optional in this scenario:

- `RATE_OFFERING`
- `RATE_UNIT_BREAK_PROFILE`
- `RATE_UNIT_BREAK`
- `ACCESSORIAL_CODE`
- `ACCESSORIAL_COST`
- `ACCESSORIAL_COST_UNIT_BREAK`
- `RATE_OFFERING_ACCESSORIAL`
- `RATE_GEO_ACCESSORIAL`
- `RATE_GEO_STOPS`

### RATE_GEO_ONLY

Tables in load order:

1. `X_LANE`
2. `RATE_GEO`
3. `ACCESSORIAL_COST`
4. `RATE_GEO_ACCESSORIAL`
5. `RATE_GEO_COST_GROUP`
6. `RATE_GEO_COST`

Required for the scenario:

- `X_LANE`
- `RATE_GEO`
- `RATE_GEO_COST_GROUP`
- `RATE_GEO_COST`

Optional in this scenario:

- `ACCESSORIAL_COST`
- `RATE_GEO_ACCESSORIAL`

Pre-existing or catalog-assisted references:

- `RATE_OFFERING`
- any reference field governed by `reference_field_policies`

### ACCESSORIAL_ONLY

Tables in load order:

1. `ACCESSORIAL_COST`
2. `RATE_OFFERING_ACCESSORIAL`
3. `RATE_GEO_ACCESSORIAL`

Required for the scenario:

- `ACCESSORIAL_COST`

Optional in this scenario:

- `RATE_OFFERING_ACCESSORIAL`
- `RATE_GEO_ACCESSORIAL`

Pre-existing or catalog-assisted references:

- `RATE_OFFERING`
- `RATE_GEO`
- `ACCESSORIAL_CODE`

## OTM CSV Rules

Every generated CSV preview must follow this table-level format:

```text
TABLE_NAME
COLUMN_1,COLUMN_2,COLUMN_3
value_1,value_2,value_3
```

If the table preview includes at least one DATE column according to the Data
Dictionary, the CSV must include the session directive before the first value
row:

```text
TABLE_NAME
COLUMN_1,DATE_COLUMN
exec alter session set nls_date_format = 'YYYY-MM-DD HH24:MI:SS'
value_1,2026-01-01 00:00:00
```

This directive belongs to the table preview, not the full batch header.

## Technical Column Handling

The first batch contract should explicitly support these table-specific rules:

| Table | Column | Rule |
|---|---|---|
| `RATE_OFFERING` | `RATE_OFFERING_SEQ` | Leave blank when present in incoming data; do not require it. |
| `RATE_GEO` | `RATE_GEO_SEQ` | Remove from generated CSV preview. It is system-generated/internal. |
| `RATE_GEO_COST_GROUP` | `RATE_GEO_COST_GROUP_SEQ` | Default to `1` when missing. |
| `RATE_GEO_COST` | `RATE_GEO_COST_SEQ` | Generate sequential values per `RATE_GEO_COST_GROUP_GID` when missing. |
| `RATE_GEO_COST` | `CHARGE_AMOUNT_BASE` | Force null/blank in technical CSV preview. |

All these columns were checked against the local 26B Data Dictionary before this
design was written. If a future OTM version changes these fields, the dictionary
reader should report the mismatch instead of silently generating invalid output.

## Data Model

### `rate_batches`

```text
id
project_id
environment_id
profile_id
scenario_code
name
description
status
source_type
domain_name
created_by
created_at
updated_at
validated_at
approved_at
exported_at
summary_json
```

Initial statuses:

```text
DRAFT
VALIDATING
VALIDATED
APPROVED
EXPORT_PREVIEWED
FAILED
```

Approval is only a backend state in this slice. It does not mean the data was
loaded into OTM.

### `rate_batch_tables`

```text
id
batch_id
table_name
sequence_index
requirement_level
row_count
status
created_at
updated_at
```

`requirement_level` values:

```text
REQUIRED
OPTIONAL
PRE_EXISTING
```

### `rate_batch_rows`

```text
id
batch_id
batch_table_id
table_name
row_index
row_payload_json
normalized_payload_json
row_hash
status
created_at
updated_at
```

The submitted row is preserved in `row_payload_json`. Derived defaults and
technical transformations are stored in `normalized_payload_json`.

### `rate_batch_issues`

```text
id
batch_id
batch_table_id
batch_row_id
severity
issue_code
table_name
column_name
message
details_json
created_at
```

Issues are append-only per validation run. Re-validation should either mark old
issues as superseded or delete and recreate issues in one transaction; the first
implementation may use delete-and-recreate for simplicity.

## Validation Contract

Validation runs in layers:

1. Scenario validation:
   - submitted scenario exists;
   - required tables for that scenario are present;
   - submitted tables are allowed for that scenario.
2. Data Dictionary validation:
   - table exists in the configured dictionary root;
   - every submitted column exists in that table;
   - DATE columns are known for CSV directive behavior.
3. Sequence validation:
   - batch tables are sorted by canonical Rates order;
   - missing parent tables inside the Rates sequence generate `ERROR`;
   - parent tables outside the Rates slice generate `WARNING`.
4. Row normalization:
   - apply technical column rules;
   - derive sequence values when required by this contract;
   - preserve submitted payload separately from normalized payload.
5. Reference policy validation:
   - reuse existing reference catalog policies where field mapping exists;
   - do not block new Rate Offerings by default;
   - duplicate Rate Offering candidates remain `WARNING`.

Batch validity:

- Any `ERROR` means batch status cannot move to `VALIDATED`.
- `WARNING` issues allow `VALIDATED`.
- `INFO` issues are informational only.

## API Contract

Initial endpoints:

```text
GET    /api/v1/modules/rates/templates
POST   /api/v1/modules/rates/batches
GET    /api/v1/modules/rates/batches
GET    /api/v1/modules/rates/batches/{batch_id}
POST   /api/v1/modules/rates/batches/{batch_id}/tables
POST   /api/v1/modules/rates/batches/{batch_id}/validate
GET    /api/v1/modules/rates/batches/{batch_id}/issues
POST   /api/v1/modules/rates/batches/{batch_id}/csv-preview
```

Deferred endpoints:

```text
POST   /api/v1/modules/rates/batches/{batch_id}/approve
POST   /api/v1/modules/rates/batches/{batch_id}/export-csv
POST   /api/v1/modules/rates/batches/{batch_id}/export-xml
GET    /api/v1/modules/rates/batches/{batch_id}/evidence
```

`csv-preview` returns technical text previews grouped by table. It does not write
final artifacts and does not claim OTM load readiness.

## Example Batch Payload

Synthetic example only:

```json
{
  "scenario_code": "RATE_GEO_ONLY",
  "name": "Synthetic OTM1 rate geo package",
  "domain_name": "OTM1",
  "tables": [
    {
      "table_name": "X_LANE",
      "rows": [
        {
          "X_LANE_GID": "OTM1.RG_DEMO_001",
          "X_LANE_XID": "RG_DEMO_001"
        }
      ]
    },
    {
      "table_name": "RATE_GEO",
      "rows": [
        {
          "RATE_GEO_GID": "OTM1.RG_DEMO_001",
          "RATE_GEO_XID": "RG_DEMO_001",
          "RATE_OFFERING_GID": "OTM1.RO_DEMO",
          "X_LANE_GID": "OTM1.RG_DEMO_001"
        }
      ]
    }
  ]
}
```

## Testing Strategy

Minimum tests for the implementation plan:

- scenarios endpoint returns all three initial scenarios;
- creating a batch stores scenario, status, domain, and metadata;
- adding tables sorts them by canonical Rates sequence;
- validation rejects an unknown table;
- validation rejects an unknown column;
- validation errors when a required scenario table is missing;
- validation warns for parent dependencies outside the Rates slice;
- `RATE_GEO.RATE_GEO_SEQ` is omitted from CSV preview;
- `RATE_GEO_COST_GROUP.RATE_GEO_COST_GROUP_SEQ` defaults to `1`;
- `RATE_GEO_COST.RATE_GEO_COST_SEQ` increments per cost group;
- `RATE_GEO_COST.CHARGE_AMOUNT_BASE` is blank in CSV preview;
- CSV preview emits the date directive when selected columns include DATE;
- synthetic domains only appear in fixtures and tests.

## Risks

The first risk is confusing CSV preview with final export. The endpoint name,
docs, and status should keep this as a preview/contract until Load Plan and
artifact generation exist.

The second risk is over-modeling tariff semantics before the real workbook is
defined. This design stores flexible JSON rows and only enforces table, column,
sequence, and minimal scenario rules.

The third risk is relying on remembered OTM behavior instead of the Data
Dictionary. Implementation must read the dictionary for every table and column
validation path.

## Decisions

- Start with backend/DB/API only.
- Use `codex/rates-batch-contract` for this work.
- Keep examples synthetic: `PUBLIC`, `OTM1`, `OTM2`.
- CSV preview comes before final CSV export.
- XML export stays deferred.
- Rate Offering creation remains allowed unless a later business rule blocks it.
- Sequence handling is canonical but still validated against the Data Dictionary.

## Next Steps

1. Review this design.
2. Write the implementation plan with TDD tasks.
3. Implement DB models and migration.
4. Implement scenario/template service.
5. Implement batch persistence and table/row ingestion.
6. Implement validation and issues.
7. Extend CSV preview to consume persisted batches.
8. Run tests, migration, and lint.

## Last Updated

2026-05-18
