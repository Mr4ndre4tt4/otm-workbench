# Evidence Hub Archive Package Design

## Context

Evidence Hub can now list evidence, show linked artifact and manifest summaries,
and download individual artifacts through an audited endpoint. The next useful
backend slice is a traceable archive package for a selected evidence set.

The archive must stay safe for MVP0: it should consolidate client-safe metadata
and references without copying raw source artifacts into the archive. Source
artifact downloads remain handled by the audited artifact download endpoint.

No OTM table dependency, CSVUTIL execution, Oracle call, UI, or cutover status
transition is introduced.

## Decision

Implement **Evidence Hub Archive Package** as a metadata archive ZIP.

Compared options:

- **Metadata-only archive:** safest and immediately useful for traceability.
- **Archive with source artifact bytes:** useful later, but it can bundle raw CSV
  or internal ZIP payloads and needs richer permission policy.
- **Cutover status transition next:** premature until evidence bundles exist.

Recommendation: metadata-only archive first.

## Goals

- Add a backend endpoint to generate an Evidence Hub archive package.
- Select evidence with filters already used by the Evidence Hub index.
- Include only client-safe evidence rows.
- Write a ZIP with deterministic JSON entries:
  - `archive_manifest.json`
  - `evidence_index.json`
  - `artifact_index.json`
  - `manifest_index.json`
- Create platform `Artifact`, `Manifest`, `Evidence`, `AuditLog`, and
  `DomainEvent` rows for the archive.
- Make the archive downloadable through the existing artifact download endpoint
  by linking it to client-safe archive evidence.

## Non-Goals

- No source artifact bytes inside the archive.
- No bulk download of source files.
- No project phase model.
- No new table or migration.
- No UI.
- No OTM upload, CSVUTIL execution, external Oracle calls, or package status
  transition.
- No real client names or real customer data in docs/tests.

## API

Create archive:

```text
POST /api/v1/evidence-hub/archive-packages
```

Request:

```json
{
  "source_module": "load_plan",
  "evidence_type": "load_plan_readiness_export",
  "status": "CREATED",
  "project_id": null,
  "sensitivity_level": "client_safe"
}
```

All fields are optional. The service always filters to `client_safe == true`.

Response:

```json
{
  "archive_id": "artifact-id",
  "artifact_id": "artifact-id",
  "manifest_id": "manifest-id",
  "evidence_id": "evidence-id",
  "file_name": "evidence_hub_archive_20260518T000000Z.zip",
  "sha256": "hash",
  "size_bytes": 123,
  "summary": {
    "evidence_count": 3,
    "artifact_ref_count": 2,
    "manifest_ref_count": 2,
    "filters": {
      "source_module": "load_plan",
      "evidence_type": "load_plan_readiness_export",
      "status": "CREATED",
      "project_id": null,
      "sensitivity_level": "client_safe"
    }
  }
}
```

Errors:

- `400`: no client-safe evidence matches the filters.

## ZIP Contract

`archive_manifest.json`:

```json
{
  "schema_version": "evidence-hub-archive-manifest/v1",
  "manifest_type": "evidence_hub_archive",
  "source_module": "evidence_hub",
  "filters": {},
  "files": [
    {"path": "evidence_index.json", "sha256": "hash", "size_bytes": 123},
    {"path": "artifact_index.json", "sha256": "hash", "size_bytes": 123},
    {"path": "manifest_index.json", "sha256": "hash", "size_bytes": 123}
  ],
  "evidence_count": 3,
  "artifact_ref_count": 2,
  "manifest_ref_count": 2,
  "generated_at": "2026-05-18T00:00:00+00:00",
  "generated_by": "admin@example.com"
}
```

`evidence_index.json` contains serialized Evidence Hub index items for the
selected evidence rows.

`artifact_index.json` contains linked artifact metadata summaries only. It does
not include `file_path`.

`manifest_index.json` contains linked manifest summaries only. It does not
include full `manifest_json`.

## Persistence

Archive artifact:

```text
Artifact.source_module = "evidence_hub"
Artifact.artifact_type = "evidence_hub_archive_zip"
Artifact.content_type = "application/zip"
Artifact.sensitivity_level = "internal"
```

Archive manifest:

```text
Manifest.source_module = "evidence_hub"
Manifest.status = "CREATED"
Manifest.manifest_json = archive_manifest_json
```

Archive evidence:

```text
Evidence.source_module = "evidence_hub"
Evidence.evidence_type = "evidence_hub_archive"
Evidence.client_safe = true
Evidence.sensitivity_level = "client_safe"
Evidence.artifact_id = archive artifact id
Evidence.manifest_id = archive manifest id
```

Audit:

```text
AuditLog.action = "evidence_hub.archive_package.create"
AuditLog.target_type = "artifact"
AuditLog.target_id = archive artifact id
```

Domain event:

```text
DomainEvent.event_type = "evidence_hub.archive_package.created"
DomainEvent.aggregate_type = "artifact"
DomainEvent.aggregate_id = archive artifact id
```

## Security And Data Safety

- Use existing authenticated route dependency for MVP0 consistency.
- Always filter evidence to `client_safe == true`.
- Do not include source artifact bytes.
- Do not include artifact `file_path`.
- Do not include full `manifest_json`.
- Do not include raw CSV row values, review decision notes, or real client names
  in archive evidence, audit, event, or response metadata.

## Implementation Notes

Extend:

```text
src/otm_workbench/evidence_hub/routes.py
```

Reuse serializers:

- `serialize_evidence_index_item`
- `serialize_artifact_summary`
- `serialize_manifest_summary`

Use helpers:

- `file_sha256` from `otm_workbench.platform.services`
- `utcnow` from `otm_workbench.models`

Use stdlib:

- `hashlib`
- `zipfile`
- `Path`

## Tests

Add backend tests with synthetic data:

- Archive rejects no matching evidence.
- Archive creates ZIP artifact, manifest, evidence, audit log, and domain event.
- ZIP contains the four expected JSON entries.
- ZIP entries exclude `file_path` and full `manifest_json`.
- Archive filters by source module, evidence type, status, project, and
  sensitivity.
- Archive evidence/audit/event do not include raw file contents or review notes.
- Archive artifact can be downloaded through the existing Evidence Hub artifact
  download endpoint.

## Risks

Users can mistake the archive for a full evidence bundle with raw source files.
Mitigation: name the manifest type `evidence_hub_archive` and explicitly include
metadata indexes only.

Archive filters can accidentally include too much. Mitigation: require
client-safe evidence and expose filters in manifest/evidence summary.

Manifest payloads can contain technical details. Mitigation: include only
manifest summaries, not raw manifest JSON.

## Next Steps

After this slice, the next likely increment is either project/phase modeling for
archive presets or cutover eligibility/status transition built on readiness and
evidence package availability.
