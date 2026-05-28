# Excluded Component Dependency Map

**Status:** active cleanup governance map
**Date:** 2026-05-28
**GitHub issue:** #239

## Purpose

Map hidden, internal, absorbed, and special frontend components before any
source removal proposal. Source may stay in the repository while normal user
exposure remains controlled by backend-owned navigation.

## Routing Rule

`frontend/src/app/routes/WorkbenchRoute.tsx` is the only app-shell route switch
for module surfaces. A hidden/internal module renders only when
`/api/v1/platform/navigation` returns a matching `NavigationItem`.

Unknown or omitted routes must continue to render `Module unavailable`.

## Component Map

| Surface | Source | Current import/render path | Current treatment | Removal status |
|---|---|---|---|---|
| Catalog Core | `frontend/src/modules/catalog/CatalogCoreView.tsx` | Exported from `frontend/src/modules/index.ts`; imported by `WorkbenchRoute.tsx`; rendered only for backend item `catalog`. | Hidden/internal Data Dictionary and dependency source. | Do not remove without a separate impact review for catalog hooks, tests, and OTM dependency workflows. |
| Evidence Hub | `frontend/src/modules/evidence/EvidenceHubView.tsx` | Exported from `frontend/src/modules/index.ts`; imported by `WorkbenchRoute.tsx`; rendered only for backend item `evidence`. | Hidden/internal evidence workspace; current evidence should remain module-local. | Do not remove while Assets, Rates, Load Plan, and other modules still create or link evidence records. |
| Admin Console | `frontend/src/modules/admin/AdminConsoleView.tsx` | Exported from `frontend/src/modules/index.ts`; imported by `WorkbenchRoute.tsx`; rendered for `settings` and legacy backend item `admin`. | Absorbed into active `/settings`; `/admin` is hidden/stale. | Not a deletion candidate until Settings has its own replacement surface or the reuse is deliberately retired. |
| Developer Tools | `frontend/src/modules/developer-tools/*.tsx` | Exported from `frontend/src/modules/index.ts`; imported by `WorkbenchRoute.tsx`; rendered only for backend item `dev_tools` and subroutes. | Internal diagnostics and Data Dictionary helper screens. | Do not remove while tests or diagnostics still rely on these route-level views. |
| Component Gallery | `frontend/src/app/routes/ComponentGalleryRoute.tsx` | Component-level test imports it directly; no longer imported by `WorkbenchRoute.tsx`. | Internal design/development utility, unavailable through app shell. | May be retained for design-system review; app-shell reintroduction requires a backend route/capability contract. |
| Coordinate Quality | In-module sections inside `frontend/src/modules/master-data/MasterDataView.tsx`; hooks/types under `frontend/src/platform/hooks/masterData.ts` and `frontend/src/platform/types/masterData.ts`. | Rendered under `/master-data/quality` when backend navigation exposes `master_data`. | Absorbed into active Master Data route family, not a top-level module. | Not a cleanup deletion candidate; keep with Master Data tests and browser evidence. |

## Current Active Dependencies

- `/settings` depends on `AdminConsoleView` today, so removing the Admin module
  source would break an active current-phase route.
- `/master-data/quality` depends on Coordinate Quality hooks, types, and UI
  sections inside `MasterDataView.tsx`; this is an active in-module workflow.
- Assets and other active modules may still call Catalog and Evidence APIs or
  link to catalog/evidence records; frontend route hiding is not backend API
  removal approval.
- Developer Tools and Catalog route components remain useful for internal
  diagnostics even though they are not current top-level acceptance evidence.

## Guarded Importers

| Importer | Hidden/internal imports | Guard |
|---|---|---|
| `frontend/src/app/routes/WorkbenchRoute.tsx` | `CatalogCoreView`, `EvidenceHubView`, `AdminConsoleView`, `DeveloperTools*` | `items.find((candidate) => isNavigationItemActive(candidate, currentPath))` gates rendering by backend navigation payload. |
| `frontend/src/app/routes/ComponentGalleryRoute.test.tsx` | `ComponentGalleryRoute` | Component-level test only; not normal app-shell exposure. |
| `frontend/src/modules/master-data/MasterDataView.tsx` | Coordinate Quality workflow code | Active Master Data subroute family under `/master-data/quality`. |

## Removal Prerequisites

Before deleting any hidden/internal component source:

- open a dedicated GitHub issue naming exact files;
- prove active route tests still pass;
- run backend navigation tests proving excluded top-level modules stay omitted;
- search for frontend imports, hooks, and test fixtures that still reference
  the source;
- document rollback path and retained backend API dependencies;
- avoid using screenshots as acceptance evidence unless live navigation matches
  the current UI phase.

## Safe Follow-Ups

- Add a shared dependency scan command or script if manual `rg` inventory starts
  drifting.
- Split Settings away from `AdminConsoleView` only through a Settings-specific
  implementation issue.
- Keep any Catalog/Evidence/Developer Tools cleanup as internal diagnostics
  work, separate from current user-facing module delivery.
