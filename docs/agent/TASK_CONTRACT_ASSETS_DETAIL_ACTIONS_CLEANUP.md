# Task Contract: Assets Detail Actions Cleanup

## Objective

Align the route-level asset detail action bar with the consolidated Assets spec.

## Original User Request

Continue with the next roadmap step after the Assets create-route cleanup.

## Interpreted Scope

- Add the missing detail-route action entries for upload, download, and archive.
- Rename ambiguous detail action labels to spec-aligned labels.
- Keep download execution guarded by the existing backend download contract.
- Keep archive as route navigation to the existing archive confirmation screen.

## Out Of Scope

- New backend endpoints.
- `/assets/:assetId/download` review route.
- Search/operator/pagination work for `/assets/library`.
- Refactoring the legacy workflow rail.

## Allowed Files Or Areas

- `frontend/src/modules/assets/AssetsLibraryView.tsx`
- `frontend/src/app/AppFunctionalAssets.test.tsx`
- `frontend/scripts/functional-assets-browser.mjs`
- `docs/agent/*`
- `docs/superpowers/plans/*`

## Protected Files Or Areas

- `OTM_RESOURCES/`
- `outputs/`
- Real client data and sensitive fixtures
- Unrelated module navigation

## Acceptance Criteria

- `/assets/:assetId` exposes `Edit metadata`, `Upload version`, `View versions`,
  `Manage links`, `Download current version`, and `Archive asset`.
- Download action on detail calls the existing backend guarded download endpoint.
- Download is disabled when the backend action/current-version state blocks it.
- Archive uses `/assets/:assetId/archive`.
- Existing Assets route tests and browser QA remain green.

## Validation Plan

- Add failing functional test assertions for the detail action bar.
- Implement minimal UI updates.
- Run focused detail test, full Assets test suite, build, browser QA, and
  `git diff --check`.
- Update validation and handoff docs.

## Risks

- A full `/assets/:assetId/download` route may still be useful later, but the
  current spec allows direct backend guarded download.

## Challenge Notes

No scope conflict. This is deliberately a small frontend acceptance cleanup.

## Decision

Proceed with TDD and avoid backend/API changes in this slice.
