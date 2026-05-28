# Task Contract: Assets Archive Route

**Status:** implemented local slice
**Date:** 2026-05-27

## Objective

Continue Assets Library route extraction by adding a dedicated archive review
screen for one asset at `/assets/:assetId/archive`.

## Original User Request

`siga com o próximo passo`

## Interpreted Scope

- Add `/assets/:assetId/archive` for archive confirmation and lifecycle impact
  review.
- Use the existing backend archive contract:
  `POST /api/v1/modules/assets/assets/{asset_id}/archive`.
- Show asset summary, current version, link count, backend-derived disabled
  state, and return paths.
- Keep `/assets/library` as the temporary functional workflow bridge.

## Out Of Scope

- Restore/retire/deprecate flows.
- New backend impact endpoint.
- Hard delete.
- Classification route refinement.
- Backend API changes.
- Real client data or protected local resources.

## Allowed Files Or Areas

- `frontend/src/modules/assets/AssetsLibraryView.tsx`
- `frontend/src/app/AppFunctionalAssets.test.tsx`
- `frontend/scripts/functional-assets-browser.mjs`
- `docs/agent/`
- `docs/superpowers/plans/`

## Protected Files Or Areas

- `OTM_RESOURCES/`
- local databases except temporary QA copies under `var/`
- unrelated modules outside Assets

## Acceptance Criteria

- `/assets/:assetId/archive` renders a route-level archive review screen.
- The route exposes `Back to Asset`, `Back to Library`, and `Cancel`.
- `Archive asset` calls the existing backend archive endpoint.
- Archived assets show blocked state and cannot be archived again.
- The route does not render the temporary Assets Library workflow rail.
- Browser QA validates live navigation before evidence capture and includes the
  direct archive route.

## Validation Plan

```powershell
npm test -- src/app/AppFunctionalAssets.test.tsx -t "asset archive route"
npm test -- src/app/AppFunctionalAssets.test.tsx
npm run build
npm run qa:functional:assets:browser
git diff --check
```

## Risks

- The route currently summarizes impact from existing detail/version/link data
  because a dedicated archive impact endpoint is still a future backend
  improvement.

## Challenge Notes

No challenge needed. This is the lifecycle route extraction requested by the
approved consolidated Assets spec.

## Decision

Proceed test-first with a narrow route-level archive confirmation screen.
