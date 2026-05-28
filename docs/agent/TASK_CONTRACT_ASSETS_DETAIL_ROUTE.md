# Task Contract: Assets Detail Route

**Status:** implemented local slice
**Date:** 2026-05-27

## Objective

Continue Assets Library completion by adding the first route-level object
inspection screen: `/assets/:assetId`.

## Interpreted Scope

- Keep `/assets` as the module hub.
- Keep `/assets/library` as the existing functional library bridge.
- Add a direct asset detail screen that shows backend-owned asset metadata,
  version history, links, lifecycle state, and visible return paths.
- Link hub asset rows to the direct detail route.

## Out Of Scope

- Dedicated edit, version upload, links, download review, archive, and
  classifications route extraction.
- Backend contract changes.
- New search operators or pagination.
- Real client data or protected local resources.

## Allowed Files Or Areas

- `frontend/src/modules/assets/AssetsLibraryView.tsx`
- `frontend/src/app/AppFunctionalAssets.test.tsx`
- `docs/agent/`

## Acceptance Criteria

- `/assets/:assetId` renders a route-level detail screen.
- The screen shows metadata, version history, links, and lifecycle state.
- The screen exposes `Back to Assets` and `Back to Library`.
- The old workflow rail does not render on the detail route.
- Existing Assets functional journey remains green.

## Validation Plan

```powershell
npm test -- src/app/AppFunctionalAssets.test.tsx -t "asset detail route"
npm test -- src/app/AppFunctionalAssets.test.tsx
npm run build
git diff --check
```

## Decision

Proceed with a narrow frontend route extraction and defer remaining lifecycle
routes to later Assets slices.
