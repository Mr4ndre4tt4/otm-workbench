# Task Contract: Assets Acceptance Create Route Cleanup

## Objective

Close the first Assets acceptance gap by making `/assets/new` a dedicated route-level create screen and removing classification authoring from asset creation.

## Original User Request

Continue with the next roadmap step after the Assets classifications routes slice.

## Interpreted Scope

- Add a route-level `/assets/new` create asset screen.
- Ensure the create asset route does not render the legacy Assets workflow rail.
- Ensure asset creation does not render classification authoring controls.
- Keep classification creation/editing only on `/assets/classifications/*`.
- Preserve the legacy workflow route as compatibility surface where not directly in conflict.

## Out Of Scope

- Backend search/operator/pagination improvements for `/assets/library`.
- Create-with-file upload support.
- Download review route at `/assets/:assetId/download`.
- Backend archive impact endpoint.
- Removing the whole legacy stateful workflow.

## Allowed Files Or Areas

- `frontend/src/modules/assets/AssetsLibraryView.tsx`
- `frontend/src/app/AppFunctionalAssets.test.tsx`
- `frontend/scripts/functional-assets-browser.mjs`
- `docs/agent/*` delivery and validation records
- `docs/superpowers/plans/*`

## Protected Files Or Areas

- `OTM_RESOURCES/`
- `outputs/`
- Real client data, real `db.xml`, and sensitive fixtures
- Unrelated modules and top-level navigation

## Acceptance Criteria

- `/assets/new` renders `Create asset` as a route-level screen with `Back to Library` and `Cancel`.
- `/assets/new` submits the existing backend asset create contract.
- `/assets/new` does not render `Assets Library workflow`.
- Asset creation screens do not render `Asset classification authoring`.
- Existing Assets route, detail, edit, versions, links, archive, and classification tests remain green.

## Validation Plan

- Add failing functional tests for `/assets/new` and classification-authoring separation.
- Run the focused tests, then the full Assets functional suite.
- Run frontend build.
- Run browser Assets QA with fresh runtime and live navigation validation.
- Update validation and handoff docs.

## Risks

- Existing long-form journey currently creates a classification from the legacy create stage; that test and browser journey must be updated to use the dedicated classification route.
- Full backend search acceptance remains a separate backend/API slice.

## Challenge Notes

This does not change project direction or scope. It is a narrow acceptance cleanup within the existing Assets consolidated spec.

## Decision

Proceed with TDD and keep the change limited to route-level create cleanup.
