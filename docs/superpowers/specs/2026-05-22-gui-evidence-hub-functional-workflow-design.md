# GUI Evidence Hub Functional Workflow Design

**Linear:** OTM-94
**Scope:** `/evidence` first functional workflow slice.

## Objective

Turn Evidence Hub from a passive evidence list into the shared workspace where
generated module evidence can be found, inspected, downloaded through guarded
backend endpoints, and archived as a client-safe package.

## Primary Story

```text
filter evidence -> inspect detail -> download guarded artifact -> create archive package
```

## Experience Pattern

```text
object list/detail + operational surfaces
```

Evidence Hub should not become a stacked dump of every metadata panel. The main
workspace is a single evidence search story:

```text
Find
Inspect
Download
Archive
```

The side panel owns the selected evidence detail, artifact/manifest references,
guarded download action, and archive result.

## Backend Contracts

```text
GET  /api/v1/evidence-hub/evidence
GET  /api/v1/evidence-hub/evidence/{evidence_id}
GET  /api/v1/evidence-hub/artifacts/{artifact_id}/download
POST /api/v1/evidence-hub/archive-packages
```

Filters are backend-owned query parameters:

```text
source_module
evidence_type
status
project_id
sensitivity_level
artifact_id
manifest_id
client_safe
```

## Guardrails

```text
- no real client data
- no local artifact paths in UI
- no raw manifest_json in UI
- artifact download must go through Evidence Hub backend endpoint
- archive package eligibility remains backend-owned
- frontend may pass explicit filters, but does not infer evidence validity
```

## Out Of Scope

```text
- full audit log explorer
- raw artifact preview
- archive package history screen
- internal/non-client-safe evidence browser
- deleting evidence, artifacts, or manifests
```

## Validation

```text
cd frontend
npm run test -- AppFunctionalEvidenceHub.test.tsx
```
