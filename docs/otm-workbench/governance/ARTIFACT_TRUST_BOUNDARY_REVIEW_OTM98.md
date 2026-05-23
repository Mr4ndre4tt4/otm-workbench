# Artifact Trust Boundary Review OTM-98

**Status:** implemented
**Date:** 2026-05-23

## Scope

This review covers backend-owned generated files, artifact metadata, Evidence
Hub downloads, and the platform helper endpoints used by synthetic tests and
module orchestration.

## Boundary

Artifact file content may live on disk, but public API responses must expose
only client-safe metadata:

- artifact id;
- source module;
- artifact type;
- file name;
- content type;
- sha256;
- size bytes;
- sensitivity level;
- guarded download URL when allowed.

The API must not expose local filesystem paths, real client values, secrets, or
raw production payloads.

## Implemented Controls

- Platform artifact registration now requires admin access.
- Platform manifest and evidence helper creation now require admin access.
- Platform artifact registration rejects files outside the configured
  `artifact_root`.
- Evidence Hub artifact download revalidates the stored artifact path against
  `artifact_root` before serving the file.
- Evidence Hub continues to require a client-safe evidence record before a
  linked artifact can be downloaded.
- Evidence Hub download responses verify the stored sha256 before returning the
  file.
- Error responses for missing, unsafe, out-of-root, or mismatched artifacts do
  not include local filesystem paths.

## Covered Routes

```text
POST /api/v1/platform/artifacts
POST /api/v1/platform/manifests
POST /api/v1/platform/evidence
GET  /api/v1/evidence-hub/artifacts/{artifact_id}/download
```

Module-specific generated artifacts still remain backend-owned. Generated
module downloads should continue to use stored sha256 checks and avoid exposing
local paths. New module download endpoints should either route through Evidence
Hub or use the same `artifact_root` path guard.

## Validation

```text
python -m pytest tests/test_evidence_hub_index.py tests/test_assets_library_links.py tests/test_operational_metadata.py -q
python -m pytest tests/test_assets_library_versions.py tests/test_project_cockpit_summary.py -q
```

Result:

```text
40 passed
11 passed
```
