# Frontend Navigation Pruning Task Contract

**Date:** 2026-05-27
**Status:** active implementation slice

## Objective

Prune the main UI navigation toward the To-Be module set without deleting
backend/internal capabilities.

## Original User Request

The user asked to continue with the next step after To-Be consolidation. The
recorded next step is frontend cleanup: remove or hide modules that will not be
attacked now, then proceed to data segregation and Settings.

## Interpreted Scope

This slice hides out-of-current-phase modules from the backend-owned main
navigation and adds Settings as the setup surface. It does not delete module
source files, backend APIs, tests, or diagnostics.

## Out Of Scope

- Deleting Catalog Core, Evidence Hub, Admin Console, Developer Tools, or
  Coordinate Quality source files.
- Database migrations.
- Rewriting Settings screens.
- Implementing client/domain and environment segregation.
- Creating fixture files.
- Updating Linear or opening a GitHub PR.

## Allowed Files Or Areas

- `src/otm_workbench/platform/navigation.py`
- `frontend/src/app/routes/WorkbenchRoute.tsx`
- `frontend/src/app/routes/moduleDescriptions.ts`
- `tests/test_modules_navigation.py`
- `docs/agent/`

## Protected Files Or Areas

- `OTM_RESOURCES/`
- module business logic under `src/otm_workbench/modules/`
- generated artifacts and local databases

## Acceptance Criteria

- Main navigation includes only Cockpit, Master Data, Rates, Load Plan,
  Integration, Order Release, Assets, and Settings.
- Main navigation excludes Catalog Core, Evidence Hub, Admin Console, and
  Developer Tools, even for admin users and even if the dev feature flag is on.
- Settings is backend-owned navigation metadata and routes to the existing
  setup surface.
- Internal APIs and module files remain present for later classification.
- Tests document the pruning behavior.

## Validation Plan

- Run targeted backend navigation tests.
- Run targeted frontend route test if adjusted.
- Run `git diff --check`.
- Review `git status --short`.

## Risks

- Existing broad frontend tests still cover historical Admin/Catalog/Evidence
  routes. Those tests may need a later classification pass instead of immediate
  deletion.
- The existing Settings implementation is still named `AdminConsoleView` in
  code; this slice may route Settings to that surface without renaming the
  component.

## Decision

Proceed with a small TDD implementation that changes main navigation exposure
only.
