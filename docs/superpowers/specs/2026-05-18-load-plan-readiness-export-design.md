# Load Plan Readiness Export Design

## Context

Load Plan now persists cutover readiness records derived from latest sequence
snapshots. The next backend slice should turn a readiness record into an
internal export artifact that can be reviewed, archived, or used by a later
download/evidence workflow.

This slice does not execute CSVUTIL, upload to OTM, call Oracle services, or
build a real OTM load package. It exports the workbench readiness assessment
only. It must not invent OTM functional rules; readiness export is a packaging
step over already persisted readiness data.

## Goal

Add backend/API support for exporting a persisted Load Plan cutover readiness
record as a client-safe ZIP artifact with manifest and evidence metadata.

## Scope

Included:

- New `LoadPlanReadinessExport` persistence model.
- Alembic migration for `load_plan_readiness_exports`.
- Export service that writes a deterministic internal ZIP under
  `artifact_root/load_plan/{package_id}/readiness_exports/{timestamp}`.
- ZIP entries:
  - `manifest.json`
  - `readiness.json`
  - `blockers.json`
- `POST /api/v1/modules/load-plan/cutover-readiness/{readiness_id}/export`.
- `GET /api/v1/modules/load-plan/cutover-readiness/exports`.
- `GET /api/v1/modules/load-plan/cutover-readiness/exports/{export_id}`.
- Client-safe `Artifact`, `Manifest`, `Evidence`, `AuditLog`, and
  `DomainEvent` records.
- README update and backend tests with synthetic data only.

Excluded:

- Download endpoint.
- Evidence Hub archive package.
- Real OTM load package.
- CSVUTIL runtime execution.
- OTM upload or external Oracle calls.
- Package status transition.
- UI.

## Export Model

Add `LoadPlanReadinessExport`:

```text
id
project_id
environment_id
profile_id
package_id
readiness_id
status
artifact_id
manifest_id
evidence_id
summary_json
exported_by
exported_at
created_at
updated_at
```

Indexes:

- `project_id`
- `environment_id`
- `profile_id`
- `package_id`
- `readiness_id`
- `status`
- `artifact_id`
- `manifest_id`
- `evidence_id`
- `exported_by`
- `exported_at`

Status values:

- `EXPORTED`

This slice is append-only. Re-exporting the same readiness record creates a new
export row and artifact.

## Export Preconditions

- Readiness record exists.
- Readiness record has `readiness_json`, `blockers_json`, and `summary_json`.
- Export is allowed for all readiness statuses: `READY`, `BLOCKED`,
  `NEEDS_REVIEW`, and `MISSING_SEQUENCE`.

Allowing non-ready exports is intentional: blocked readiness reports are useful
as evidence and for review. The export must clearly preserve the readiness
status so it cannot be mistaken for approval.

## ZIP Contract

`manifest.json`:

```json
{
  "schema_version": "load-plan-readiness-export-manifest/v1",
  "manifest_type": "load_plan_readiness_export",
  "source_module": "load_plan",
  "source_entity_type": "load_plan_cutover_readiness",
  "source_entity_id": "...",
  "package_id": "...",
  "readiness_status": "BLOCKED",
  "exported_at": "...",
  "exported_by": "admin@example.com",
  "entries": [
    {"path": "readiness.json", "sha256": "...", "size_bytes": 123},
    {"path": "blockers.json", "sha256": "...", "size_bytes": 123}
  ],
  "summary": {}
}
```

`readiness.json`:

- Serialized readiness record:
  - ids;
  - status;
  - readiness payload;
  - summary;
  - generated metadata;
  - evidence id.

`blockers.json`:

- Array of client-safe blockers from the readiness record.

No raw CSV row values, review decision notes, or real client names should be
written into the ZIP, artifact metadata, evidence, audit metadata, or events.

## API Contract

`POST /api/v1/modules/load-plan/cutover-readiness/{readiness_id}/export`

Response:

```json
{
  "id": "...",
  "package_id": "...",
  "readiness_id": "...",
  "status": "EXPORTED",
  "artifact_id": "...",
  "manifest_id": "...",
  "evidence_id": "...",
  "summary": {
    "readiness_status": "BLOCKED",
    "blocker_count": 2,
    "error_count": 2,
    "warning_count": 0,
    "entry_count": 3
  },
  "exported_by": "admin@example.com",
  "exported_at": "..."
}
```

`GET /api/v1/modules/load-plan/cutover-readiness/exports`

- Optional filters: `package_id`, `readiness_id`, `status`.
- Returns `PageResponse`.

`GET /api/v1/modules/load-plan/cutover-readiness/exports/{export_id}`

- Returns one export record.

## Artifact, Manifest, Evidence

Artifact:

```text
source_module: load_plan
artifact_type: load_plan_readiness_export_zip
content_type: application/zip
sensitivity_level: internal
```

Manifest:

```text
source_module: load_plan
status: CREATED
manifest_json: manifest payload
```

Evidence:

```text
source_module: load_plan
evidence_type: load_plan_readiness_export
client_safe: true
sensitivity_level: client_safe
summary_json:
  source_entity_type: load_plan_readiness_export
  source_entity_id
  package_id
  readiness_id
  readiness_status
  artifact_id
  manifest_id
  blocker_count
  error_count
  warning_count
```

Audit:

- `load_plan.readiness_export.export`

Domain event:

- `load_plan.readiness_export.exported`

## Errors

- `404`: readiness record or export record does not exist.
- `400`: readiness record has invalid JSON payloads or cannot be exported.

Use existing FastAPI route style and client-safe messages.

## Data Safety

- Do not use real client names in docs, tests, audit logs, or events.
- Use synthetic identifiers such as `OTM1`, `PUBLIC`, and `DEMO`.
- Do not store raw CSV row values in export metadata, evidence, audit metadata,
  or domain events.
- Do not copy review decision notes into export metadata.
- The artifact is marked `internal`; evidence summary remains client-safe.

## Testing

Add backend tests with synthetic data only:

- `load_plan_readiness_exports` table exists after metadata reset.
- Export rejects missing readiness id.
- Export creates ZIP artifact, manifest, evidence, audit log, and domain event.
- ZIP contains `manifest.json`, `readiness.json`, and `blockers.json`.
- ZIP manifest entry hashes and sizes match generated payloads.
- Export works for blocked readiness and preserves `readiness_status`.
- Re-exporting the same readiness creates a second export row and artifact.
- List/detail/filter endpoints work.
- Evidence/audit/event payloads do not include raw row values or decision notes.

## Security And Permissions

Use the existing authenticated route dependency for this slice, matching current
Load Plan endpoints. Later hardening can introduce capability checks for
readiness export and download actions.

## Risks

Export can be mistaken for real cutover approval. Mitigation: preserve
`readiness_status` and do not change package status.

Export can be mistaken for an OTM load package. Mitigation: artifact type and
manifest type explicitly say readiness export, not CSVUTIL or OTM upload.

Sensitive details can leak into metadata. Mitigation: write only client-safe
summaries to evidence/audit/event and keep artifact sensitivity as `internal`.

## Implementation Notes

Prefer a focused module:

- `src/otm_workbench/modules/load_plan/readiness_export.py`

Reuse:

- `serialize_cutover_readiness` from `load_plan.readiness`.
- `file_sha256`, `iso_now`, and `utc_timestamp` helpers from
  `otm_workbench.modules.rates.exports`.

The next slice after this should be either a download endpoint for exported
artifacts or an Evidence Hub archive package, depending on which workflow is
more important next.
