# Frontend Route Inventory

## Current Decision

The main UI is backend-owned. A frontend route may render as a top-level module
only when `/api/v1/platform/navigation` returns its module item for the current
user/session.

Source files for excluded or internal surfaces may remain in the repository
temporarily, but they are not accepted main-navigation evidence.

## Active Main UI Routes

These routes are in the current UI phase and may appear in sidebar navigation:

| Module ID | Route | Frontend surface | Status |
|---|---|---|---|
| `home` | `/home` | `CockpitContent` inside `WorkbenchRoute.tsx` | active |
| `master_data` | `/master-data` | `MasterDataView.tsx` | active |
| `rates` | `/rates` | `RatesSummaryView.tsx` | active |
| `load_plan` | `/load-plan` | `LoadPlanView.tsx` | active |
| `assets` | `/assets` | `AssetsLibraryView.tsx` | active |
| `order_release_generator` | `/order-release-generator` | `OrderReleaseGeneratorView.tsx` | active |
| `integration_mapping` | `/integration-mapping` | `IntegrationMappingView.tsx` | active, reserved for separate workstream |
| `settings` | `/settings` | `AdminConsoleView.tsx` reused as Settings surface | active |

## Excluded From Top-Level Navigation

These surfaces exist in source, but are not top-level UI modules for this
phase. Direct URL access must resolve to the unknown route unless the backend
navigation contract deliberately returns the module item.

| Module ID | Route | Frontend surface | Current classification |
|---|---|---|---|
| `catalog` | `/catalog` | `CatalogCoreView.tsx` | internal backend dependency, not top-level UI |
| `evidence` | `/evidence` | `EvidenceHubView.tsx` | module-local evidence dependency, not top-level UI |
| `admin` | `/admin` | `AdminConsoleView.tsx` | absorbed into Settings for current UI phase |
| `dev_tools` | `/dev-tools` | `DeveloperTools*.tsx` | developer-only/internal diagnostics |

## Special Routes

| Route | Surface | Classification |
|---|---|---|
| `/__gui/component-gallery` | `ComponentGalleryRoute.tsx` | internal design/development utility |
| unknown route | `UnknownRoute` in `WorkbenchRoute.tsx` | route recovery screen |

## Guardrails

- Do not use screenshots as acceptance evidence until the live backend
  `/api/v1/platform/navigation` response is checked against the current UI phase
  module IDs.
- Do not reintroduce Catalog Core, Evidence Hub, Admin Console / Jobs,
  Developer Tools, Coordinate Quality, or generic dashboards as top-level
  modules without a scope decision.
- Do not delete excluded route source files in this inventory slice. Deletion
  requires a separate cleanup task contract, tests, and impact review.
- Treat Integration Mapping as reserved for its dedicated workstream unless the
  latest user instruction explicitly asks for it or a minimal cross-module fix
  is required.

## Validation Coverage

- `tests/test_modules_navigation.py` verifies backend navigation returns only
  the approved current UI phase module IDs.
- `frontend/src/app/routes/WorkbenchRoute.test.tsx` verifies direct excluded
  route paths remain unavailable when backend navigation does not expose them.
