# Task Contract: Assets Links Route

**Status:** implemented local slice
**Date:** 2026-05-27

## Objective

Continue Assets Library route extraction by adding a dedicated link management
screen for one asset at `/assets/:assetId/links`.

## Original User Request

`siga com o próximo passo`

## Interpreted Scope

- Add `/assets/:assetId/links` for reviewing and creating links for one asset.
- Use the existing backend `GET/POST /api/v1/modules/assets/assets/{asset_id}/links`
  contracts.
- Reuse backend-owned link classifications and guided target choices already
  available in the module.
- Keep artifact/evidence target safety backend-owned and preserve current
  Evidence Hub target filters.
- Keep `/assets/library` as the temporary functional workflow bridge.

## Out Of Scope

- New backend target lookup endpoints.
- Link deletion/editing.
- Per-link detail routes.
- Archive review route extraction.
- Classification route refinement.
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

- `/assets/:assetId/links` renders a route-level relationship editor.
- The route shows existing asset links and direct return paths.
- The route creates a link through the existing backend contract.
- The route does not render the temporary Assets Library workflow rail.
- Browser QA validates live navigation before evidence capture and includes the
  direct links route.

## Validation Plan

```powershell
npm test -- src/app/AppFunctionalAssets.test.tsx -t "asset links route"
npm test -- src/app/AppFunctionalAssets.test.tsx
npm run build
npm run qa:functional:assets:browser
git diff --check
```

## Risks

- The current frontend still derives guided target choices locally from
  navigation, Catalog Core, Data Dictionary, and Evidence Hub. A dedicated
  backend target lookup remains a later backend/API improvement.
- The temporary workflow bridge still owns some link form code until the full
  Assets route extraction is complete.

## Challenge Notes

No challenge needed. This is the next approved Assets route extraction slice.

## Decision

Proceed test-first with a narrow route-level frontend extraction.
