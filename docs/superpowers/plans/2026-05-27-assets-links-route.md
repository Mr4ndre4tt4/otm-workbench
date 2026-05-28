# Assets Links Route Plan

## Goal

Add a route-level link management screen for `/assets/:assetId/links`.

## Tasks

- [x] Define the task contract and route boundary.
- [x] Add a failing functional test for direct link management.
- [x] Render existing links and selected asset context on the direct route.
- [x] Render link creation controls using the existing backend contract.
- [x] Extend browser QA to create a link through the direct route and capture
  evidence.
- [x] Run build, functional, browser, and diff validation.
- [x] Update validation and handoff docs with final results.

## Result

- `/assets/:assetId/links` now renders a route-level relationship editor.
- The direct route shows existing links, selected asset context, and return
  paths.
- Link creation uses the existing backend `POST` contract and backend-owned
  link type classifications.
- The route does not show the temporary Assets Library workflow rail.
- Browser QA now captures `var/qa/assets-links-route.png`.

## Validation Commands

```powershell
npm test -- src/app/AppFunctionalAssets.test.tsx -t "asset link"
npm test -- src/app/AppFunctionalAssets.test.tsx
npm run build
npm run qa:functional:assets:browser
git diff --check
```
