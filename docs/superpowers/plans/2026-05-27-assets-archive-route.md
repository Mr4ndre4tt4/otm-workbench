# Assets Archive Route Plan

## Goal

Add a route-level archive review screen for `/assets/:assetId/archive`.

## Tasks

- [x] Define the task contract and route boundary.
- [x] Add a failing functional test for direct archive review.
- [x] Render asset summary, current-version/link impact, and return paths.
- [x] Wire `Archive asset` to the existing backend archive contract.
- [x] Extend browser QA to archive through the direct route and capture
  evidence.
- [x] Run build, functional, browser, and diff validation.
- [x] Update validation and handoff docs with final results.

## Result

- `/assets/:assetId/archive` now renders a route-level archive review screen.
- The screen shows status, current version file/id, version count, linked target
  count, and backend-owned archive eligibility.
- `Archive asset` calls the existing backend archive endpoint and blocks after
  the asset is archived.
- Browser QA now archives through the direct route and captures
  `var/qa/assets-archive-route.png`.

## Validation Commands

```powershell
npm test -- src/app/AppFunctionalAssets.test.tsx -t "archives an asset"
npm test -- src/app/AppFunctionalAssets.test.tsx
npm run build
npm run qa:functional:assets:browser
git diff --check
```
