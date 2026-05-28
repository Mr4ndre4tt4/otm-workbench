# Task Contract: Assets Edit Metadata Route

**Status:** implemented local slice
**Date:** 2026-05-27

## Objective

Continue Assets Library route extraction by adding a dedicated metadata edit
screen at `/assets/:assetId/edit`.

## Interpreted Scope

- Keep `/assets` as the module hub.
- Keep `/assets/library` as the temporary functional workflow bridge.
- Keep `/assets/:assetId` as the route-level inspection screen.
- Add `/assets/:assetId/edit` for metadata-only asset updates.
- Expose direct return paths to the asset detail route and the library route.
- Preserve the existing workflow edit path until later slices remove the
  bridge.

## Out Of Scope

- Version upload route extraction.
- Link management route extraction.
- Classification management route extraction.
- Archive/review route extraction.
- Backend contract changes.
- New asset search operators or pagination.
- Real client data or protected local resources.

## Allowed Files Or Areas

- `frontend/src/modules/assets/AssetsLibraryView.tsx`
- `frontend/src/app/AppFunctionalAssets.test.tsx`
- `frontend/scripts/functional-assets-browser.mjs`
- `docs/agent/`
- `docs/superpowers/plans/`

## Acceptance Criteria

- `/assets/:assetId/edit` renders a route-level metadata edit screen.
- The legacy Assets workflow rail does not render on the direct edit route.
- `Save metadata` patches the asset through the existing backend API contract.
- The route exposes `Back to Asset` and `Back to Library`.
- Browser QA validates live navigation before evidence capture and includes the
  direct edit route.
- Existing Assets functional journey remains green.

## Validation Plan

```powershell
npm test -- src/app/AppFunctionalAssets.test.tsx -t "edits asset metadata"
npm test -- src/app/AppFunctionalAssets.test.tsx
npm run build
npm run qa:functional:assets:browser
git diff --check
```

## Decision

Proceed with a narrow frontend route extraction using the existing asset patch
contract, and keep versions, links, classifications, and archive review as the
next route-level slices.
