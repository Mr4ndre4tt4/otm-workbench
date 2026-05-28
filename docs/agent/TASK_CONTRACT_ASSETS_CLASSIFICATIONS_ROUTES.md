# Task Contract: Assets Classifications Routes

## Objective

Refine Assets Library classification management into route-level screens for listing, creating, and editing asset classifications.

## Original User Request

Continue with the next roadmap step after the Assets archive route slice.

## Interpreted Scope

- Add a dedicated `/assets/classifications` route-level screen.
- Add a dedicated `/assets/classifications/new` route-level create screen.
- Add a dedicated `/assets/classifications/:classificationId/edit` route-level edit screen when the backend allows updates.
- Keep route entry points clear from the Assets hub and library.
- Preserve existing backend-owned classification contracts.

## Out Of Scope

- Removing the legacy in-flow classification bridge from asset creation.
- Changing backend classification validation semantics.
- Adding new top-level modules or bringing excluded modules back into the sidebar.
- Committing or publishing `OTM_RESOURCES/`.

## Allowed Files Or Areas

- `frontend/src/modules/assets/AssetsLibraryView.tsx`
- `frontend/src/app/AppFunctionalAssets.test.tsx`
- `frontend/scripts/functional-assets-browser.mjs`
- `docs/agent/*` delivery and validation records
- `docs/superpowers/plans/*`

## Protected Files Or Areas

- `OTM_RESOURCES/`
- Client data, real `db.xml`, and sensitive fixtures
- Unrelated modules and navigation scope

## Acceptance Criteria

- `/assets/classifications` shows classification groups and route entry points without showing the Assets Library workflow.
- `/assets/classifications/new` creates a classification through `POST /api/v1/modules/assets/classifications`.
- `/assets/classifications/:classificationId/edit` saves editable fields through `PATCH /api/v1/modules/assets/classifications/{classification_id}`.
- System-protected classifications are visibly guarded from editing.
- Focused functional tests cover list, create, and edit routes.
- Browser QA evidence verifies the live navigation scope before screenshot capture.

## Validation Plan

- Run focused failing tests before implementation.
- Run focused tests after implementation.
- Run the full Assets functional test file.
- Run frontend build.
- Run browser QA for the Assets route journey on fresh ports and a fresh QA database.
- Update validation and handoff documentation.

## Risks

- Existing legacy create-stage classification authoring may still be used by older tests or flows; this slice keeps it as a compatibility bridge.
- Classifications are loaded as grouped data, not through a detail endpoint, so edit routes resolve the selected classification from the grouped list.

## Challenge Notes

No scope conflict found. This is a narrow continuation of the approved Assets route-level cleanup.

## Decision

Proceed with TDD and keep the diff limited to Assets classification routes and related evidence.
