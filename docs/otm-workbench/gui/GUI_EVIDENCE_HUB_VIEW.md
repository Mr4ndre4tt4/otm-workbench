# GUI Evidence Hub View

**Status:** implemented
**Branch:** `codex/gui-evidence-hub-view`

## Objective

Add the first backend-backed Evidence Hub screen using the shared GUI
foundation.

Evidence Hub now renders evidence index and selected evidence detail from
backend contracts instead of the generic module placeholder.

## Backend Contracts

The GUI consumes:

```text
GET /api/v1/evidence-hub/evidence
GET /api/v1/evidence-hub/evidence/{evidence_id}
```

## GUI Behavior

The screen uses shared components:

```text
- MetricGrid for evidence, artifact, manifest, and client-safe counters;
- ModuleObjectList for selectable evidence records;
- SelectedObjectPanel for selected evidence metadata;
- DetailList for artifact and manifest references.
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

This slice intentionally does not add archive package creation or artifact
download actions to the GUI. Those can be wired later through backend-owned
available actions or explicit guarded endpoints.

## Validation

Commands executed:

```text
cd frontend
npm run test -- App.test.tsx
npm run lint
npm run test
npm run build
```
