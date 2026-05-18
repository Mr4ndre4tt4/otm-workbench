# Rates Batch Approval And Readiness Gate Design

## Context

The Rates module now supports:

- reference catalog and Data Dictionary-backed validation;
- persisted Rates batches with tables, rows, and issues;
- technical CSV preview;
- internal CSV export ZIP artifacts with manifest, evidence, and audit.

The foundation docs already define `POST /api/v1/modules/rates/batches/{batch_id}/approve`
and the capability `rates.batch.approve`, but the backend does not yet implement
an approval/readiness gate for Rates batches.

This slice adds that backend gate. It does not add UI, Load Plan records,
CSVUTIL, real OTM upload, or cutover readiness.

## Goal

Add backend/API support for approving a Rates batch after validation/export
readiness checks, recording the decision with audit and client-safe evidence.

Approval means:

```text
The Rates batch has passed the module-level checks required to be considered
approved for downstream review/export workflows.
```

Approval does not mean:

```text
The data was loaded into OTM.
The package is ready for cutover.
The Load Plan accepted it.
```

## Scope

Included:

- `POST /api/v1/modules/rates/batches/{batch_id}/approve`.
- Approval preconditions based on status and issues.
- Optional approval note.
- `approved_at` timestamp on `RateBatch`.
- `approved_by` stored inside batch `summary_json` because the current DB model
  does not yet have an `approved_by` column.
- Audit log entry for `rates.batch.approve`.
- Domain event `rates.batch.approved`.
- Client-safe evidence record `rates_batch_approval`.
- `GET /api/v1/modules/rates/batches/{batch_id}/readiness`.
- Readiness response summarizing status, blockers, issue counts, export artifact
  presence, and allowed next actions.

Excluded:

- New database migration.
- UI.
- Role/capability enforcement beyond current authenticated-user dependency.
- Real OTM upload.
- CSVUTIL/Load Plan package creation.
- Cutover readiness.
- XML export.

## Approval Preconditions

Approval should be allowed when:

- batch exists;
- batch has at least one table and at least one row;
- latest validation/export issue state has zero `ERROR` issues;
- batch status is one of:
  - `VALIDATED`
  - `EXPORT_PREVIEWED`
  - `EXPORTED`

Approval should be rejected when:

- batch is `DRAFT`;
- batch has persisted `ERROR` issues;
- batch has no tables or rows;
- batch is already `APPROVED`, unless the request is explicitly idempotent.

Idempotency decision:

- Calling approve on an already approved batch should return `200` with the
  current approval state and should not create duplicate evidence/audit/event.

Warnings do not block approval. They remain visible in readiness and evidence
summary.

## Readiness Contract

Add:

```text
GET /api/v1/modules/rates/batches/{batch_id}/readiness
```

Response:

```json
{
  "batch_id": "batch_id",
  "status": "EXPORTED",
  "ready_for_approval": true,
  "ready_for_export": true,
  "issue_summary": {
    "errors": 0,
    "warnings": 2,
    "infos": 0
  },
  "table_count": 2,
  "row_count": 3,
  "has_export_artifact": true,
  "blockers": [],
  "next_actions": ["approve"]
}
```

Blocker examples:

```text
BATCH_NOT_VALIDATED
HAS_ERROR_ISSUES
NO_TABLES
NO_ROWS
ALREADY_APPROVED
```

`ready_for_export` remains true for `VALIDATED`, `EXPORT_PREVIEWED`, and
`APPROVED` batches with no errors. Export itself still owns artifact generation.

## Approval Response

`POST /approve` response:

```json
{
  "batch_id": "batch_id",
  "status": "APPROVED",
  "approved_at": "2026-05-18T14:00:00",
  "approved_by": "admin@example.com",
  "evidence_id": "evidence_id",
  "readiness": {
    "ready_for_approval": true,
    "blockers": []
  }
}
```

If approval is rejected:

```json
{
  "code": "HTTP_ERROR",
  "message": "Rate batch has ERROR issues and cannot be approved.",
  "details": {}
}
```

## Evidence Contract

Create one `Evidence` row on first approval:

```text
source_module = "rates"
evidence_type = "rates_batch_approval"
status = CREATED
client_safe = true
sensitivity_level = client_safe
artifact_id = latest rates_csv_zip artifact id, if present
manifest_id = latest rates_csv_export manifest id, if present
```

`summary_json`:

```json
{
  "source_entity_type": "rate_batch",
  "source_entity_id": "batch_id",
  "scenario_code": "ACCESSORIAL_ONLY",
  "domain_name": "OTM1",
  "approved_by": "admin@example.com",
  "approved_at": "2026-05-18T14:00:00",
  "issue_summary": {
    "errors": 0,
    "warnings": 2,
    "infos": 0
  },
  "table_count": 1,
  "row_count": 1,
  "has_export_artifact": true,
  "approval_note": "Reviewed for CRP package"
}
```

Evidence must not contain raw row values, CSV text, charges, lane payloads, or
full table payload JSON.

## Audit And Event

Audit:

```text
action = "rates.batch.approve"
target_type = "rate_batch"
target_id = batch_id
metadata_json = {
  "evidence_id": "...",
  "approved_by": "...",
  "issue_summary": {...}
}
```

Domain event:

```text
event_type = "rates.batch.approved"
source_module = "rates"
aggregate_type = "rate_batch"
aggregate_id = batch_id
payload_json = {
  "evidence_id": "...",
  "approved_by": "...",
  "status": "APPROVED"
}
status = "PENDING"
```

## Capability Note

The architecture names `rates.batch.approve`, but the current auth/capability
layer does not yet provide a module-level dependency for capability checks. This
slice should not build a broad RBAC system. It should require authentication and
record `approved_by`; capability enforcement can be added when platform
capability dependencies are available.

Tests should verify authenticated access and business preconditions, not full
role matrix yet.

## Testing Strategy

Minimum tests:

- readiness returns blockers for a draft batch;
- readiness returns issue counts and table/row counts;
- approval rejects draft batch;
- approval rejects batch with `ERROR` issues;
- approval succeeds for `VALIDATED` or `EXPORTED` batch with warnings only;
- approval sets status `APPROVED` and `approved_at`;
- approval stores `approved_by` and note in `summary_json`;
- approval creates client-safe evidence without raw row values;
- approval creates audit log `rates.batch.approve`;
- approval creates domain event `rates.batch.approved`;
- repeated approval is idempotent and does not duplicate evidence/audit/event.

## Risks

Approval can be mistaken for Load Plan or cutover readiness. Mitigation: endpoint
and evidence text call this module-level approval only.

Approval evidence can leak raw tariff payloads. Mitigation: evidence stores
counts, statuses, references, and issue summaries only.

Capability behavior can be overbuilt too early. Mitigation: record the intended
capability and keep enforcement for a later platform capability dependency.

## Decisions

- No migration in this slice.
- Store `approved_by` and `approval_note` in `RateBatch.summary_json`.
- Allow approval with warnings.
- Reject approval with errors.
- Make repeated approval idempotent.
- Create evidence/audit/event only on the first successful approval.

## Next Steps

1. Write TDD implementation plan.
2. Implement readiness service and endpoint.
3. Implement approval service and endpoint.
4. Add evidence, audit, and event creation.
5. Verify tests, Alembic, and Ruff.

## Last Updated

2026-05-18
