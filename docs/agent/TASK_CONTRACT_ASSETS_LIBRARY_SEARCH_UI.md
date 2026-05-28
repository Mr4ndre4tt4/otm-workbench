# Task Contract: Assets Library Search UI

## Objective

Make `/assets/library` consume the backend-owned search/operator/pagination
contract added for Assets Library.

## In Scope

- Add search inputs for asset name and description.
- Add operator controls for name, description, module id, macro object, and OTM
  table.
- Keep existing classification/status/scope/tag filters.
- Add page size and basic page navigation controls.
- Update the Assets functional test and browser QA script.
- Preserve route-level Assets workflows and selected-asset behavior.

## Out Of Scope

- Integration Mapping implementation work.
- Link target type search.
- Target OTM version search.
- New backend API behavior.
- Generic dashboard or excluded-module navigation changes.

## Acceptance Criteria

- Applying search sends backend-owned text filter and operator query params.
- Reset search clears search values, restores default operators, and returns to
  the default asset list URL.
- Pagination metadata is visible on `/assets/library`.
- Assets functional tests and browser QA pass.
- Browser QA navigation evidence remains inside the current UI phase.

## Validation

- `npm test -- src/app/AppFunctionalAssets.test.tsx`
- `npm run build`
- `npm run qa:functional:assets:browser`
- `git diff --check`

## Risks

- The UI still does not expose linked target type or target OTM version search;
  those remain future backend/UI slices.
