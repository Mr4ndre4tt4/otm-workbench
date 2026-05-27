# Frontend Navigation Pruning Report

**Status:** implemented first cleanup slice
**Date:** 2026-05-27

## Objective

Start frontend cleanup by pruning the backend-owned main navigation to the
current To-Be UI phase, without deleting source modules or backend/internal
capabilities.

## What Changed

Main navigation now exposes only:

1. Master Data / Data Factory
2. Project Cockpit
3. Rates Studio
4. Load Plan
5. Assets Library
6. Order Release Generator
7. Integration Mapping Studio
8. Settings

The following are no longer exposed in main navigation:

- Catalog Core;
- Evidence Hub;
- Admin Console;
- Developer Tools.

`Settings` is now the backend-owned setup surface at `/settings`. It currently
routes to the existing setup implementation that was previously named
`AdminConsoleView`; the file/component rename is intentionally deferred to
avoid a broad refactor in this cleanup slice.

## Files Changed

- `src/otm_workbench/platform/navigation.py`
- `frontend/src/app/routes/WorkbenchRoute.tsx`
- `frontend/src/app/routes/moduleDescriptions.ts`
- `frontend/src/modules/admin/AdminConsoleView.tsx`
- `tests/test_modules_navigation.py`
- `frontend/src/app/App.test.tsx`

## Validation

Targeted tests:

```text
pytest tests/test_modules_navigation.py -q
npm test -- src/app/App.test.tsx -t "routes backend-owned Settings navigation"
```

Expected:

- backend navigation includes `settings`;
- backend navigation excludes `catalog`, `evidence`, `admin`, and `dev_tools`;
- enabling the `dev_tools` feature flag does not reintroduce Developer Tools to
  the main navigation;
- `/settings` renders the setup surface instead of the generic module
  placeholder.

## Deliberately Deferred

- deleting old frontend module files;
- renaming `AdminConsoleView` source file to `SettingsView`;
- rewriting historical Admin/Catalog/Evidence/Developer Tools tests;
- removing backend APIs used as internal dependencies;
- full Cockpit redesign to remove recent jobs/evidence dashboard behavior.

## Next Step

Plan client/domain and environment segregation before continuing Settings to
completion.
