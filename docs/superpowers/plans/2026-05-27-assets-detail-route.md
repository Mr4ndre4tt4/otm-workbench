# Assets Detail Route Plan

## Goal

Add the first route-level Assets Library object screen for `/assets/:assetId`.

## Tasks

- [x] Define the task contract and route scope.
- [x] Add a failing functional test for direct asset detail navigation.
- [x] Render asset detail metadata, versions, links, lifecycle state, and
  return paths.
- [x] Link hub asset rows to `/assets/:assetId`.
- [x] Preserve the existing `/assets/library` workflow.
- [x] Run final build and diff validation.
- [x] Update validation and handoff docs with final results.

## Result

- `/assets/:assetId` now renders an `Asset detail` route-level screen.
- Hub rows link to asset detail with `Open detail`.
- The route shows backend-owned metadata, version history, linked workbench
  objects, lifecycle status, and return paths.
- `/assets/library` still preserves the existing functional workflow bridge.

## Validation Commands

```powershell
npm test -- src/app/AppFunctionalAssets.test.tsx -t "asset detail route"
npm test -- src/app/AppFunctionalAssets.test.tsx
npm run build
git diff --check
```
