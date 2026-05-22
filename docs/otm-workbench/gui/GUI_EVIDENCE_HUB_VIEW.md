# GUI Evidence Hub View

**Status:** first functional slice delivered
**Branch:** `codex/gui-evidence-hub-view`
**Linear:** OTM-94

## Objective

Added the first backend-backed Evidence Hub workflow using the shared GUI
foundation.

Evidence Hub renders evidence index/detail from backend contracts and
orchestrates the first operational story:

```text
filter evidence -> inspect detail -> download guarded artifact -> create archive package
```

## Backend Contracts

The GUI consumes:

```text
GET /api/v1/evidence-hub/evidence
GET /api/v1/evidence-hub/evidence/{evidence_id}
GET /api/v1/evidence-hub/artifacts/{artifact_id}/download
POST /api/v1/evidence-hub/archive-packages
```

## GUI Behavior

The screen uses shared components:

```text
- MetricGrid for evidence, artifact, manifest, and client-safe counters;
- a compact workflow strip for Find, Inspect, Download, Archive;
- filter controls backed by evidence list query parameters;
- ModuleObjectList for selectable evidence records;
- SelectedObjectPanel for selected evidence metadata and actions;
- DetailList for artifact, manifest, and latest archive references.
```

The first selected evidence defaults to the first backend item. Selecting
another evidence record updates the detail query through backend-owned ids.

## Safety

```text
- No client-specific sample data in tests or docs.
- No raw evidence payload rendering.
- No local file path rendering.
- No manifest JSON rendering.
- No frontend-only lifecycle or permission decisions.
- Evidence status, source module, sensitivity, artifact, and manifest metadata come from backend contracts.
```

Artifact download and archive creation use Evidence Hub backend endpoints. The
frontend does not display artifact local paths or raw manifest payloads.

## Validation

Commands executed:

```text
cd frontend
npm run test -- AppFunctionalEvidenceHub.test.tsx
npm run qa:functional:evidence:browser
npm run lint
npm run build
```
