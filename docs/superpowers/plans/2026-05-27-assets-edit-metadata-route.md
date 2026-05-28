# Assets Edit Metadata Route Plan

## Goal

Add a route-level metadata edit screen for `/assets/:assetId/edit`.

## Tasks

- [x] Define the task contract and route boundary.
- [x] Add a failing functional test for direct metadata editing.
- [x] Render a metadata-only edit workspace with clear return paths.
- [x] Wire `Save metadata` to the existing asset patch contract.
- [x] Link the asset detail route to `/assets/:assetId/edit`.
- [x] Extend browser QA to visit and submit the direct edit route.
- [x] Run build, functional, browser, and diff validation.
- [x] Update validation and handoff docs with final results.

## Result

- `/assets/:assetId/edit` now renders a dedicated metadata edit screen.
- The direct edit route does not show the temporary Assets workflow rail.
- `Save metadata` updates the selected asset through the existing backend API.
- The route exposes `Back to Asset` and `Back to Library`.
- Browser QA now captures `var/qa/assets-edit-metadata-route.png` after a
  direct metadata update.

## Validation Commands

```powershell
npm test -- src/app/AppFunctionalAssets.test.tsx -t "edits asset metadata"
npm test -- src/app/AppFunctionalAssets.test.tsx
npm run build
npm run qa:functional:assets:browser
git diff --check
```
