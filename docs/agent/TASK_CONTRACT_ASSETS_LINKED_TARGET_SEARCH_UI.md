# Task Contract: Assets Linked Target Search UI

## Objective

Expose the backend-owned Assets Library `linked target type` filter on
`/assets/library`.

## In Scope

- Add a linked target type select sourced from existing asset link
  classifications.
- Add a linked target type operator select for `one_of` and `not_one_of`.
- Send `linked_target_type` and `linked_target_type_operator` through the
  existing Assets filter query serialization.
- Update the Assets functional test and browser QA script.

## Out Of Scope

- Backend API changes.
- Target OTM version search.
- Storybook stories, because this is a small in-context form extension and the
  existing functional/browser coverage is the stronger validation path.
- Integration Mapping implementation work.

## Acceptance Criteria

- Applying search includes linked target type params in the assets list URL.
- Reset search clears linked target type and restores `one_of`.
- Assets functional test, build, browser QA, and diff checks pass.

## Validation

- `npm test -- src/app/AppFunctionalAssets.test.tsx -t "creates an asset, uploads a version"`
- `npm test -- src/app/AppFunctionalAssets.test.tsx`
- `npm run build`
- `npm run qa:functional:assets:browser`
- `git diff --check`
