# Evidence Hub Artifact Download Design

## Context

Evidence Hub now provides a backend-only index and detail API for client-safe
evidence with linked artifact and manifest summaries. The next missing
contract is controlled artifact download: users can see that an artifact exists,
but there is no canonical way to retrieve the file through Evidence Hub.

The foundation design already calls out artifact downloads as sensitive
operations that must be audited. This slice adds that behavior without changing
module-specific generation logic.

No OTM table dependency or CSVUTIL behavior is introduced. Evidence Hub reads
already-persisted artifact metadata only.

## Decision

Implement **Evidence Hub Artifact Download** as a narrow backend endpoint.

Compared options:

- **Artifact download now:** small, testable, and directly builds on the Evidence
  Hub Index.
- **Archive package first:** useful later, but it depends on multiple-download
  packaging and phase selection.
- **Cutover status transition first:** premature until artifacts can be retrieved
  and audited through the canonical evidence surface.

Recommendation: implement artifact download now.

## Goals

- Add a download endpoint under Evidence Hub.
- Stream an existing artifact file by artifact id.
- Require an existing client-safe `Evidence` record linked to that artifact.
- Recompute the file hash before serving and reject mismatches.
- Audit every successful download.
- Keep errors client-safe and avoid exposing filesystem paths.

## Non-Goals

- No archive package generation.
- No bulk download.
- No UI.
- No OTM upload, CSVUTIL execution, external Oracle calls, or package status
  transition.
- No new table or migration.
- No real client names or real customer data in docs/tests.

## API

Download:

```text
GET /api/v1/evidence-hub/artifacts/{artifact_id}/download
```

Success:

- Returns the artifact bytes.
- Uses the artifact `content_type`.
- Uses `Content-Disposition: attachment; filename="<artifact.file_name>"`.
- Adds `X-Artifact-SHA256` with the persisted hash.

Errors:

- `404`: artifact does not exist, has no client-safe evidence link, or file is
  missing on disk.
- `409`: file exists but its SHA-256 no longer matches persisted metadata.

Use generic client-safe messages. Do not include `artifact.file_path` in error
responses.

## Eligibility

An artifact is downloadable when:

- `Artifact.id == artifact_id`.
- At least one `Evidence` row references `artifact_id`.
- That evidence row has `client_safe == true`.

This keeps the endpoint evidence-driven instead of exposing arbitrary artifact
metadata rows.

## Audit

Create one `AuditLog` row after a successful download:

```text
action = "evidence_hub.artifact.download"
target_type = "artifact"
target_id = artifact.id
actor_user_id = user.email
```

Metadata:

```json
{
  "artifact_id": "artifact-id",
  "artifact_type": "rates_csv_zip",
  "source_module": "rates",
  "evidence_id": "evidence-id",
  "sha256": "hash",
  "size_bytes": 123
}
```

Do not include file paths, raw file contents, raw CSV values, or review decision
notes in audit metadata.

## Security And Permissions

Use the existing authenticated route dependency for MVP0 consistency. Later
hardening can replace this with a dedicated capability such as
`evidence.artifact.download`.

MVP0 behavior:

- Authenticated users can download artifacts only through client-safe evidence.
- Artifacts without client-safe evidence are not downloadable through this
  endpoint.
- Missing files and unauthorized artifacts both return generic 404-style errors
  to avoid exposing local storage details.

## Data Safety

- Tests use synthetic identifiers such as `OTM1` and generated ids.
- The response body may contain artifact bytes by definition.
- Error responses and audit records must not expose file paths or raw contents.
- The endpoint does not inspect ZIP internals or parse OTM data.

## Implementation Notes

Extend:

```text
src/otm_workbench/evidence_hub/routes.py
```

Use:

- `FileResponse` from `fastapi.responses`.
- `Path` from stdlib.
- `file_sha256` from `otm_workbench.platform.services`.
- Existing `Artifact`, `Evidence`, `AuditLog`, and `User` models.

No new service module is required unless the route grows later.

## Tests

Add backend tests with synthetic files:

- Download requires authentication.
- Download rejects missing artifact id.
- Download rejects artifacts without client-safe evidence.
- Download rejects missing file without leaking path.
- Download rejects hash mismatch with `409`.
- Download returns bytes, content type, disposition filename, and hash header.
- Successful download creates audit log.
- Audit metadata does not include file path or raw file contents.

## Risks

Serving a file without checking evidence could expose arbitrary local artifact
rows. Mitigation: require a client-safe evidence link.

Files can change after artifact metadata is persisted. Mitigation: recompute
SHA-256 before streaming and reject mismatches.

Error responses can leak local paths. Mitigation: use generic messages and tests
that assert path absence.

## Next Steps

After this slice, the next likely increment is Evidence Hub archive package by
project or operational phase.
