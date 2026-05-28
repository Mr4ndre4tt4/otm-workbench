# Task Contract: Assets Library Row Actions

## Objective

Expose route-level row actions from `/assets/library` so users can open an
asset, upload a version, or archive directly from search results.

## In Scope

- Replace the library result renderer with rows that support explicit actions.
- Add row-level `Open`, `Upload version`, and `Archive` links.
- Preserve local `Select` behavior for the existing workflow panels.
- Add functional coverage for row action destinations.
- Validate the full Assets functional journey, build, and browser QA.

## Out Of Scope

- Backend API changes.
- Integration Mapping implementation work.
- Link target type or target OTM version search.
- New archive, upload, or detail behavior beyond existing routes.

## Acceptance Criteria

- Each visible result exposes an `Open <asset>` link to `/assets/:assetId`.
- Each eligible result exposes `Upload version for <asset>` to
  `/assets/:assetId/versions/new`.
- Each eligible result exposes `Archive <asset>` to `/assets/:assetId/archive`.
- Selecting a result still updates the in-page selected asset workflow state.
- Assets functional tests, build, browser QA, and diff checks pass.

## Validation

- `npm test -- src/app/AppFunctionalAssets.test.tsx -t "library row actions"`
- `npm test -- src/app/AppFunctionalAssets.test.tsx`
- `npm run build`
- `npm run qa:functional:assets:browser`
- `git diff --check`
