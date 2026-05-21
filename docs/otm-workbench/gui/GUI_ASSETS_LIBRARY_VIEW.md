# GUI Assets Library View

**Status:** implemented
**Branch:** `codex/gui-assets-library-view`

## Objective

Add the first backend-backed module screen after Rates using the shared GUI
foundation.

Assets Library now renders real backend contracts instead of the generic module
placeholder.

## Backend Contracts

The GUI consumes:

```text
GET /api/v1/modules/assets/assets
GET /api/v1/modules/assets/assets/{asset_id}
GET /api/v1/modules/assets/assets/{asset_id}/versions
```

## GUI Behavior

The screen uses shared components:

```text
- MetricGrid for asset counters;
- ModuleObjectList for selectable assets;
- SelectedObjectPanel for selected asset metadata;
- DetailList for asset versions.
```

The first selected asset defaults to the first backend item. Selecting another
asset updates the detail and versions queries through backend-owned ids.

## Safety

```text
- No client-specific sample data in tests or docs.
- No local file/storage path rendering.
- No frontend-only lifecycle or permission decisions.
- Asset status, classifications, table linkage, and version status come from backend contracts.
```

This slice intentionally does not add create, upload, archive, or download
actions to the GUI. Those can be wired later through backend-owned available
actions or explicit guarded endpoints.

## Validation

Commands executed:

```text
cd frontend
npm run test -- App.test.tsx
npm run lint
npm run test
npm run build
```
