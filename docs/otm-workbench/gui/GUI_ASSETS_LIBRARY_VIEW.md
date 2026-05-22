# GUI Assets Library View

**Status:** functional slice implemented
**Branch:** `codex/gui-foundation-integration-pr-plan`

## Objective

Assets Library now renders a backend-backed lifecycle workflow instead of only
listing asset metadata.

## Backend Contracts

The GUI consumes:

```text
GET /api/v1/modules/assets/assets
POST /api/v1/modules/assets/assets
GET /api/v1/modules/assets/assets/{asset_id}
POST /api/v1/modules/assets/assets/{asset_id}/archive
GET /api/v1/modules/assets/assets/{asset_id}/download
GET /api/v1/modules/assets/assets/{asset_id}/versions
POST /api/v1/modules/assets/assets/{asset_id}/versions
GET /api/v1/modules/assets/assets/{asset_id}/links
POST /api/v1/modules/assets/assets/{asset_id}/links
```

## GUI Behavior

The screen uses shared components:

```text
- MetricGrid for asset counters;
- ModuleObjectList for selectable assets;
- SelectedObjectPanel for selected asset metadata;
- A staged workflow for Library -> Create -> Version -> Link -> Lifecycle;
- OperationalPanel for the active create, upload, link, or lifecycle action;
- DetailList for asset versions and links;
- FeedbackMessage for backend action results.
```

The first selected asset defaults to the first backend item. Selecting another
asset updates detail, versions, and links through backend-owned ids. The current
functional slice follows a staged story: review the Library, create a
client-safe synthetic support asset, upload a file version, create a module
link, download the current version through the guarded backend download
endpoint, and archive the asset. Once the backend returns `ARCHIVED`, the UI
keeps lifecycle actions disabled for new uploads and links.

## Safety

```text
- No client-specific sample data in tests or docs.
- No local file/storage path rendering.
- No frontend-only lifecycle or permission decisions.
- Asset status, classifications, table linkage, version status, links, download
  permission/audit, and archive state come from backend contracts.
```

Still open:

```text
- richer custom metadata editing
- advanced filters
- arbitrary link authoring beyond the current module-link slice
- deeper authoring for backend-owned classifications, tags, visibility, scope,
  sensitivity, OTM table links, and macro-object links
```

## Validation

Commands executed:

```text
cd frontend
npm run qa:functional:assets
npm run qa:functional:assets:browser
npm run test -- src/app/AppFunctionalAssets.test.tsx
npm run lint
npm run build
python -m pytest tests/test_assets_library_foundation.py tests/test_assets_library_assets.py tests/test_assets_library_versions.py tests/test_assets_library_links.py tests/test_assets_library_permissions.py
```
