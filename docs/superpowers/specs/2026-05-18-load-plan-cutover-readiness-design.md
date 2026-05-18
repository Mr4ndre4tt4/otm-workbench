# Load Plan Cutover Readiness Design

## Context

Load Plan now has backend slices for package intake, CSVUTIL artifact
generation, ZIP Analysis, setup review queue decisions, and sequence snapshots
with blockers. The next slice can produce a cutover readiness view by
consolidating the latest sequence snapshot for each package and exposing a
client-safe readiness status.

This slice is still backend/API-only. It does not execute CSVUTIL, upload data
to OTM, call Oracle services, or export a cutover package. It also does not
invent OTM functional rules. Readiness is derived from artifacts already stored
inside the workbench. If an OTM-specific technical or functional question is
not covered by local context or official Oracle documentation, do not encode it
as behavior without asking.

## Goal

Add backend/API support for generating a persisted cutover readiness assessment
from Load Plan packages and their latest sequence snapshots.

## Scope

Included:

- New `LoadPlanCutoverReadiness` persistence model.
- Alembic migration for `load_plan_cutover_readiness`.
- Readiness service that evaluates one package or all packages.
- `POST /api/v1/modules/load-plan/cutover-readiness/generate`.
- `GET /api/v1/modules/load-plan/cutover-readiness`.
- `GET /api/v1/modules/load-plan/cutover-readiness/{readiness_id}`.
- `GET /api/v1/modules/load-plan/cutover-readiness/latest?package_id=...`.
- Client-safe evidence, audit log, and domain event for generated readiness.
- README update and backend tests with synthetic data only.

Excluded:

- Readiness export/download.
- Cutover execution.
- CSVUTIL runtime execution.
- OTM upload, external Oracle calls, or live OTM validation.
- Package status transition.
- UI.
- Cross-environment validation.

## Readiness Model

Add `LoadPlanCutoverReadiness`:

```text
id
project_id
environment_id
profile_id
package_id
sequence_snapshot_id
status
readiness_json
blockers_json
summary_json
evidence_id
generated_by
generated_at
created_at
updated_at
```

Indexes:

- `project_id`
- `environment_id`
- `profile_id`
- `package_id`
- `sequence_snapshot_id`
- `status`
- `evidence_id`
- `generated_by`
- `generated_at`

Status values:

- `READY`: latest sequence snapshot exists and has no blockers.
- `BLOCKED`: latest sequence snapshot exists and has one or more error
  blockers.
- `NEEDS_REVIEW`: latest sequence snapshot exists and has warning blockers but
  no error blockers.
- `MISSING_SEQUENCE`: no sequence snapshot exists for the package.

`READY` means ready for the later workbench cutover export flow, not proof that
OTM will accept a load.

## Readiness Derivation

Input:

- Optional `package_id`.
- If omitted, generate readiness for all registered Load Plan packages.

For each package:

1. Find latest `LoadPlanSequenceSnapshot` for the package.
2. If no sequence snapshot exists, create readiness with
   `status="MISSING_SEQUENCE"` and a `SEQUENCE_SNAPSHOT_MISSING` blocker.
3. If latest snapshot has error blockers, create readiness with
   `status="BLOCKED"`.
4. If latest snapshot has only warning blockers, create readiness with
   `status="NEEDS_REVIEW"`.
5. If latest snapshot has no blockers, create readiness with `status="READY"`.

Readiness payload:

```json
{
  "package_id": "...",
  "sequence_snapshot_id": "...",
  "status": "BLOCKED",
  "checks": [
    {
      "code": "SEQUENCE_SNAPSHOT_AVAILABLE",
      "status": "PASSED",
      "message": "Latest sequence snapshot is available."
    },
    {
      "code": "NO_ERROR_BLOCKERS",
      "status": "FAILED",
      "message": "Latest sequence snapshot contains error blockers."
    }
  ]
}
```

Blockers:

- Copy client-safe blockers from the latest sequence snapshot.
- Add `SEQUENCE_SNAPSHOT_MISSING` when no snapshot exists.
- Do not copy raw CSV row values, decision notes, or real client names.

Summary:

```json
{
  "package_count": 1,
  "ready_count": 0,
  "blocked_count": 1,
  "needs_review_count": 0,
  "missing_sequence_count": 0,
  "blocker_count": 2,
  "error_count": 2,
  "warning_count": 0,
  "next_actions": ["resolve_sequence_blockers"]
}
```

Next actions:

- `generate_sequence_snapshot`: no sequence snapshot exists.
- `resolve_sequence_blockers`: error blockers exist.
- `review_warnings`: warning blockers exist and no error blockers exist.
- `ready_for_cutover_export`: no blockers exist.

## API Contract

`POST /api/v1/modules/load-plan/cutover-readiness/generate`

Request:

```json
{
  "package_id": "..."
}
```

`package_id` is optional. If omitted, generate one readiness record per
registered package and return an aggregate response.

Response:

```json
{
  "items": [
    {
      "id": "...",
      "package_id": "...",
      "sequence_snapshot_id": "...",
      "status": "BLOCKED",
      "readiness": {},
      "blockers": [],
      "summary": {},
      "evidence_id": "...",
      "generated_by": "admin@example.com",
      "generated_at": "..."
    }
  ],
  "summary": {
    "package_count": 1,
    "ready_count": 0,
    "blocked_count": 1,
    "needs_review_count": 0,
    "missing_sequence_count": 0,
    "blocker_count": 2,
    "error_count": 2,
    "warning_count": 0,
    "next_actions": ["resolve_sequence_blockers"]
  }
}
```

`GET /api/v1/modules/load-plan/cutover-readiness`

- Optional filters: `package_id`, `status`.
- Returns `PageResponse`.

`GET /api/v1/modules/load-plan/cutover-readiness/{readiness_id}`

- Returns one readiness record.

`GET /api/v1/modules/load-plan/cutover-readiness/latest?package_id=...`

- Returns latest readiness for a package.
- Returns 404 when no readiness exists.

## Evidence And Events

Create client-safe evidence for each readiness record:

```text
source_module: load_plan
evidence_type: load_plan_cutover_readiness
summary_json:
  source_entity_type: load_plan_cutover_readiness
  source_entity_id
  package_id
  sequence_snapshot_id
  status
  blocker_count
  error_count
  warning_count
```

Audit:

- `load_plan.cutover_readiness.generate`

Domain event:

- `load_plan.cutover_readiness.generated`

Do not copy raw CSV row values or review decision notes into evidence, audit
metadata, events, or response examples.

## Errors

- `404`: requested package or readiness record does not exist.
- `400`: no registered packages exist when generating aggregate readiness.

Use existing FastAPI route style and client-safe messages.

## Data Safety

- Do not use real client names in docs, tests, audit logs, or events.
- Use synthetic identifiers such as `OTM1`, `PUBLIC`, and `DEMO`.
- Do not store raw CSV row values in readiness, evidence, audit metadata, or
  domain events.
- Do not copy review decision notes into readiness blockers.
- Do not infer OTM acceptance from `READY`.

## Testing

Add backend tests with synthetic data only:

- `load_plan_cutover_readiness` table exists after metadata reset.
- Generate readiness rejects a missing package.
- Generate aggregate readiness rejects when no packages exist.
- Package without sequence snapshot creates `MISSING_SEQUENCE` readiness.
- Package with latest blocked sequence snapshot creates `BLOCKED` readiness.
- Package with warning-only sequence snapshot creates `NEEDS_REVIEW` readiness.
- Package with blocker-free sequence snapshot creates `READY` readiness.
- Evidence, audit log, and domain event are created for generated readiness.
- List, detail, filters, and latest endpoint work.
- Aggregate generation creates one readiness record per registered package.
- Evidence/audit/event payloads do not include raw row values or decision notes.

## Security And Permissions

Use the existing authenticated route dependency for this slice, matching current
Load Plan endpoints. Later hardening can introduce capability checks for
readiness generation and future export actions.

## Risks

`READY` can be mistaken for OTM validation. Mitigation: documentation and
response semantics say it is readiness for later workbench cutover export only.

Readiness can duplicate sequence blocker logic. Mitigation: this slice consumes
latest sequence snapshots and does not recalculate Data Dictionary or review
decision blockers.

Export can creep into this slice. Mitigation: no export endpoint or artifact is
included here; export should be the next slice after readiness generation.

## Implementation Notes

Prefer a new focused module:

- `src/otm_workbench/modules/load_plan/readiness.py`

Keep route additions in the existing Load Plan router. Reuse
`latest_sequence_snapshot` and `serialize_sequence_snapshot` concepts from
`load_plan.sequence`, but do not duplicate its derivation rules.

The next slice after this should be Cutover Readiness Export, built on persisted
readiness records.
