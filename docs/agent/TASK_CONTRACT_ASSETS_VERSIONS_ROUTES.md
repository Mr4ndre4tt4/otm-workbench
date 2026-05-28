# Task Contract: Assets Versions Routes

**Status:** implemented local slice
**Date:** 2026-05-27

## Objective

Continue Assets Library route extraction by adding dedicated version history and
version upload routes for one asset.

## Original User Request

`siga com o próximo passo`

## Interpreted Scope

- Add `/assets/:assetId/versions` for version history and current-version
  state.
- Add `/assets/:assetId/versions/new` for uploading a new version for one
  asset.
- Keep download guarded by the existing backend current-version download
  contract.
- Keep `/assets/library` as the temporary functional workflow bridge.
- Keep `/assets/:assetId` and `/assets/:assetId/edit` intact.

## Out Of Scope

- Asset link management route extraction.
- Classification route refinement.
- Archive review route extraction.
- Per-version download endpoint changes.
- Backend API contract changes.
- New dependencies.
- Real client data or protected local resources.

## Allowed Files Or Areas

- `frontend/src/modules/assets/AssetsLibraryView.tsx`
- `frontend/src/app/AppFunctionalAssets.test.tsx`
- `frontend/scripts/functional-assets-browser.mjs`
- `docs/agent/`
- `docs/superpowers/plans/`

## Protected Files Or Areas

- `OTM_RESOURCES/`
- real client data, screenshots, fixtures, seeds, or local databases
- unrelated modules outside Assets

## Acceptance Criteria

- `/assets/:assetId/versions` renders a route-level version history screen.
- `/assets/:assetId/versions/new` renders a route-level upload screen.
- Neither route renders the temporary Assets Library workflow rail.
- The version history route exposes `Back to Asset`, `Back to Library`, and
  `Upload new version`.
- The upload route uses the existing backend version upload contract and shows
  backend disabled state for archived/non-uploadable assets.
- Browser QA validates live navigation before evidence capture and includes the
  direct versions routes.

## Validation Plan

```powershell
npm test -- src/app/AppFunctionalAssets.test.tsx -t "asset versions route"
npm test -- src/app/AppFunctionalAssets.test.tsx -t "uploads an asset version on a direct route"
npm test -- src/app/AppFunctionalAssets.test.tsx
npm run build
npm run qa:functional:assets:browser
git diff --check
```

## Risks

- The current backend only exposes current-version download; per-version
  download should not be implied until a backend contract exists.
- Route extraction must not break the existing workflow bridge while downstream
  slices still rely on it.

## Challenge Notes

No challenge needed. The task matches the approved Assets route extraction
roadmap and keeps behavior inside the current frontend/API contracts.

## Decision

Proceed with test-first frontend route extraction and documentation updates.
