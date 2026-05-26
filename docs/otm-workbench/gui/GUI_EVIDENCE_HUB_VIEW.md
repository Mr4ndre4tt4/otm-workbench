# GUI Evidence Hub View

**Status:** functional slice delivered plus archive history and filter reset recovery; superseded for future UX direction by `GUI_EVIDENCE_HUB_CONSOLIDATED_SPEC.md`
**Branch:** `codex/master-data-hardening-next`
**Linear:** OTM-94

## Objective

Added the first backend-backed Evidence Hub workflow using the shared GUI
foundation.

Evidence Hub renders evidence index/detail from backend contracts and
orchestrates the first operational story:

```text
filter evidence -> inspect detail -> download guarded artifact -> create archive package -> review archive history -> switch evidence with clean operation feedback
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
- reset recovery for filter controls, clearing draft/applied filter state,
  selected evidence, archive preview state, and reloading the backend evidence
  list without query parameters;
- ModuleObjectList for selectable evidence records;
- SelectedObjectPanel for selected evidence metadata and actions;
- DetailList for artifact, manifest, and latest archive references.
```

The first selected evidence defaults to the first backend item. Selecting
another evidence record updates the detail query through backend-owned ids and
clears operation feedback, operation errors, and artifact download state from
the previously selected evidence. Archive history remains backend-owned and is
not tied to a single selected record.

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

Archive package history is also backend-owned. The GUI reads
`evidence_hub_archive` evidence records created by Evidence Hub instead of
keeping a frontend-only archive list.

The filter bar uses `Apply filters` and `Reset filters` instead of silently
relying on route reloads. React and browser QA both assert that reset clears all
filter inputs and returns to the unfiltered backend list before continuing the
download/archive workflow.

Evidence selection recovery is also covered: after creating an archive package,
selecting another evidence record must not leave stale archive/download feedback
visible as if it belonged to the newly selected record.

## Validation

Commands executed:

```text
cd frontend
npm run test -- AppFunctionalEvidenceHub.test.tsx
npm run qa:functional:evidence:browser
npm run lint
npm run build
```
