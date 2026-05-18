# Load Plan Package Intake Design

## Context

The Rates module can now:

- create persisted synthetic tariff batches;
- validate submitted OTM tables against the local Data Dictionary;
- generate internal CSV ZIP artifacts with manifest and client-safe evidence;
- approve batches with readiness checks, approval evidence, audit, and domain event.

The roadmap says Load Plan should consume packages from Rates and Data Factory,
then later add CSVUTIL, ZIP analysis, setup review, load sequence, and cutover
readiness. This slice starts only the package intake contract.

It does not load data into OTM and does not claim cutover readiness.

## Goal

Add backend/API support for registering approved Rates exports as Load Plan
packages, so Load Plan can list candidate packages and preserve links to the
source batch, export artifact, manifest, and approval evidence.

## Scope

Included:

- New `LoadPlanPackage` persistence model.
- Alembic migration for `load_plan_packages`.
- `POST /api/v1/modules/load-plan/packages/from-rates/{batch_id}`.
- `GET /api/v1/modules/load-plan/packages`.
- `GET /api/v1/modules/load-plan/packages/{package_id}`.
- Idempotent intake: registering the same Rates batch twice returns the same
  package and does not duplicate audit/event/evidence.
- Audit log entry for `load_plan.package.register_from_rates`.
- Domain event `load_plan.package.registered`.
- Client-safe evidence `load_plan_package_intake`.
- Summary endpoint `GET /api/v1/modules/load-plan/summary`.

Excluded:

- CSVUTIL CTL/CL generation.
- ZIP analysis.
- Setup review queue.
- Load Plan execution history.
- Cutover readiness.
- Real OTM upload.
- XML export.
- UI.
- Data Factory package intake.

## Data Dictionary Usage

The service should inspect source Rates batch tables and load sequence metadata
already validated from `OTM_RESOURCES/DATA_DICT26B/data_dictionary/json/data_dict`.
It should not parse arbitrary CSV text or infer table order from ZIP contents.

Load sequence stored on the package should come from `RateBatchTable.sequence_index`
and table names already created by the Rates module. Future CSVUTIL generation
will use that sequence to build CTL/CL files. If a future package includes any
date-bearing OTM table exports, CSV files still follow the existing rule:

```text
table name line
column header line
exec alter session set nls_date_format = 'YYYY-MM-DD HH24:MI:SS'
value lines
```

This slice records package metadata only; it does not generate new OTM CSV
content.

## Model Contract

Add `LoadPlanPackage`:

```text
id
project_id
environment_id
profile_id
source_module
source_entity_type
source_entity_id
package_type
status
artifact_id
manifest_id
evidence_id
approval_evidence_id
load_sequence_json
summary_json
created_by
registered_at
created_at
updated_at
```

Initial values for Rates intake:

```text
source_module = "rates"
source_entity_type = "rate_batch"
source_entity_id = RateBatch.id
package_type = "rates_csv_zip"
status = "REGISTERED"
artifact_id = latest rates_csv_zip Artifact id
manifest_id = matching rates_csv_export Manifest id
evidence_id = new load_plan_package_intake Evidence id
approval_evidence_id = latest rates_batch_approval Evidence id
```

`load_sequence_json` example:

```json
[
  {
    "position": 10,
    "table_name": "ACCESSORIAL_COST",
    "row_count": 1,
    "requirement_level": "OPTIONAL"
  }
]
```

`summary_json` example:

```json
{
  "source_module": "rates",
  "source_batch_id": "batch_id",
  "scenario_code": "ACCESSORIAL_ONLY",
  "domain_name": "OTM1",
  "source_status": "APPROVED",
  "package_type": "rates_csv_zip",
  "table_count": 1,
  "row_count": 1,
  "has_export_artifact": true,
  "has_approval_evidence": true
}
```

Evidence and package summaries must not contain raw row values, CSV text, charge
amounts, lane payloads, or real client identifiers.

## Intake Preconditions

Rates batch intake should be allowed when:

- batch exists;
- batch status is `APPROVED`;
- latest `rates_csv_export` evidence exists;
- latest export evidence has both `artifact_id` and `manifest_id`;
- latest `rates_batch_approval` evidence exists;
- batch has at least one table and at least one row.

Reject when:

- batch does not exist: 404;
- batch is not `APPROVED`: 400;
- no export artifact/manifest exists: 400;
- no approval evidence exists: 400;
- batch has no tables or no rows: 400.

The endpoint should be idempotent. If a `LoadPlanPackage` already exists for
`source_module="rates"` and `source_entity_id=batch_id`, return it with `200`
and do not create another evidence/audit/event record.

## API Contract

### Register From Rates

```text
POST /api/v1/modules/load-plan/packages/from-rates/{batch_id}
```

Response:

```json
{
  "id": "load_package_id",
  "source_module": "rates",
  "source_entity_type": "rate_batch",
  "source_entity_id": "batch_id",
  "package_type": "rates_csv_zip",
  "status": "REGISTERED",
  "artifact_id": "artifact_id",
  "manifest_id": "manifest_id",
  "evidence_id": "evidence_id",
  "approval_evidence_id": "approval_evidence_id",
  "load_sequence": [
    {
      "position": 10,
      "table_name": "ACCESSORIAL_COST",
      "row_count": 1,
      "requirement_level": "OPTIONAL"
    }
  ],
  "summary": {
    "source_module": "rates",
    "scenario_code": "ACCESSORIAL_ONLY",
    "domain_name": "OTM1",
    "table_count": 1,
    "row_count": 1
  }
}
```

### List Packages

```text
GET /api/v1/modules/load-plan/packages
```

Response uses existing `PageResponse`:

```json
{
  "items": [
    {
      "id": "load_package_id",
      "source_module": "rates",
      "source_entity_id": "batch_id",
      "package_type": "rates_csv_zip",
      "status": "REGISTERED",
      "artifact_id": "artifact_id",
      "manifest_id": "manifest_id"
    }
  ],
  "total": 1
}
```

### Get Package

```text
GET /api/v1/modules/load-plan/packages/{package_id}
```

Returns the package plus parsed `load_sequence` and `summary`.

### Summary

```text
GET /api/v1/modules/load-plan/summary
```

Response:

```json
{
  "registered_packages": 1,
  "by_source_module": {
    "rates": 1
  },
  "by_status": {
    "REGISTERED": 1
  },
  "next_actions": ["build_csvutil"]
}
```

`build_csvutil` is only a next action label. It does not mean this slice has
implemented CSVUTIL.

## Evidence Contract

Create one `Evidence` row on first intake:

```text
source_module = "load_plan"
evidence_type = "load_plan_package_intake"
status = CREATED
client_safe = true
sensitivity_level = client_safe
artifact_id = rates export artifact id
manifest_id = rates export manifest id
```

`summary_json`:

```json
{
  "source_entity_type": "load_plan_package",
  "source_entity_id": "load_package_id",
  "upstream_source_module": "rates",
  "upstream_entity_type": "rate_batch",
  "upstream_entity_id": "batch_id",
  "package_type": "rates_csv_zip",
  "artifact_id": "artifact_id",
  "manifest_id": "manifest_id",
  "approval_evidence_id": "approval_evidence_id",
  "table_count": 1,
  "row_count": 1
}
```

Do not copy Rates row payloads, CSV file contents, ZIP contents, or manifest file
details into this evidence summary.

## Audit And Event

Audit:

```text
action = "load_plan.package.register_from_rates"
target_type = "load_plan_package"
target_id = package_id
metadata_json = {
  "source_module": "rates",
  "source_entity_id": "batch_id",
  "artifact_id": "...",
  "manifest_id": "...",
  "evidence_id": "..."
}
```

Domain event:

```text
event_type = "load_plan.package.registered"
source_module = "load_plan"
aggregate_type = "load_plan_package"
aggregate_id = package_id
payload_json = {
  "source_module": "rates",
  "source_entity_id": "batch_id",
  "package_type": "rates_csv_zip",
  "status": "REGISTERED"
}
status = "PENDING"
```

## Capability Note

The broader security model names Load Plan capabilities such as
`load_plan.csvutil.generate`, but the current API only has the shared
authenticated-user dependency. This slice should require authentication and
record `created_by`. Full role/capability enforcement can be added when module
capability dependencies are available.

## Testing Strategy

Minimum tests:

- register rejects a non-approved Rates batch;
- register rejects an approved batch with no CSV export artifact;
- register rejects an exported but unapproved batch;
- register succeeds for an approved Rates batch with CSV export evidence;
- package links export artifact, export manifest, and approval evidence;
- package `load_sequence_json` follows Rates table sequence order;
- package and evidence summaries are client-safe and exclude raw row values;
- list packages returns registered packages;
- get package returns parsed load sequence and summary;
- summary endpoint returns package counts by status and source module;
- repeated register is idempotent and does not duplicate package/evidence/audit/event;
- Alembic upgrade creates `load_plan_packages`.

## Risks

Load Plan package intake can be confused with CSVUTIL generation. Mitigation:
use `REGISTERED` status and `load_plan_package_intake` evidence; do not create
CSVUTIL artifacts or execution records in this slice.

Load Plan can be confused with cutover readiness. Mitigation: no cutover tables,
endpoints, blockers, or readiness manifests in this slice.

Evidence can leak raw tariff data. Mitigation: store only counts, source IDs,
artifact IDs, manifest IDs, statuses, and table names.

## Decisions

- Start with Rates-only package intake.
- Store load sequence as JSON on `LoadPlanPackage`, using existing Rates table
  sequence.
- Use one package per source Rates batch.
- Keep ZIP artifact sensitivity as defined by Rates export; Load Plan package
  evidence remains client-safe.
- Do not create `LoadPlan` records yet. The package list can exist before a named
  operational load plan.

## Next Steps

1. Write a TDD implementation plan.
2. Add `LoadPlanPackage` model and migration.
3. Add `modules/load_plan` service and routes.
4. Register the new router in `main.py`.
5. Add package intake, listing, detail, summary tests.
6. Run tests, Alembic, and Ruff.

## Last Updated

2026-05-18
