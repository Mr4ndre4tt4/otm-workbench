# Assets Versions Routes Plan

## Goal

Add route-level version history and upload screens for Assets.

## Tasks

- [x] Define the task contract and route boundary.
- [x] Add failing functional tests for `/assets/:assetId/versions` and
  `/assets/:assetId/versions/new`.
- [x] Render version history with current-version/download state and return
  paths.
- [x] Render direct version upload with backend disabled state.
- [x] Extend browser QA to visit, upload through, and screenshot the direct
  versions routes.
- [x] Run build, functional, browser, and diff validation.
- [x] Update validation and handoff docs with final results.

## Result

- `/assets/:assetId/versions` now renders route-level version history with
  current-version state, guarded current-version download, and return paths.
- `/assets/:assetId/versions/new` now renders route-level version upload with
  backend-owned disabled state.
- The temporary Assets Library workflow rail does not render on either direct
  versions route.
- Browser QA now captures `var/qa/assets-versions-route.png` and
  `var/qa/assets-version-upload-route.png`.

## Validation Commands

```powershell
npm test -- src/app/AppFunctionalAssets.test.tsx -t "asset versions route"
npm test -- src/app/AppFunctionalAssets.test.tsx -t "uploads an asset version on a direct route"
npm test -- src/app/AppFunctionalAssets.test.tsx
npm run build
npm run qa:functional:assets:browser
git diff --check
```
