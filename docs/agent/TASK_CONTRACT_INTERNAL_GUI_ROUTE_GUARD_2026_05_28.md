# Task Contract: Internal GUI Route Guard

**Date:** 2026-05-28
**GitHub issue:** #235
**Status:** validated

## Objective

Keep internal GUI utility routes behind the backend-owned navigation contract so
direct app-shell access cannot show excluded tools during the current frontend
cleanup phase.

## In Scope

- Guard `/__gui/component-gallery` through the normal `WorkbenchRoute`
  unavailable state when backend navigation does not expose it.
- Preserve the standalone component gallery component and its direct component
  test for internal design-system work.
- Update focused frontend route/app tests.
- Update validation and handoff docs.

## Out of Scope

- Deleting the component gallery implementation.
- Removing Catalog, Evidence, Admin, or Developer Tools source modules.
- Browser screenshot evidence.
- Integration Mapping behavior.

## Acceptance Criteria

- `/__gui/component-gallery` renders `Module unavailable` through the app shell
  when the backend navigation payload omits it.
- Existing excluded route recovery coverage remains green.
- The slice introduces no real client data and no destructive cleanup.

## Validation Plan

- `npm test -- src/app/routes/WorkbenchRoute.test.tsx src/app/AppComponentGalleryRoute.test.tsx`
- `git diff --check`

## Risks

- Existing component-gallery development can still use
  `ComponentGalleryRoute.test.tsx`, but shell access now requires an explicit
  future backend contract if the route is ever reintroduced.
