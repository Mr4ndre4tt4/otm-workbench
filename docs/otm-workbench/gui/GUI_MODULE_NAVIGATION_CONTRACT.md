# GUI Module Navigation Contract

**Status:** delivered  
**Branch:** `codex/gui-module-navigation-contract`  
**Scope:** frontend contract guardrail for module ids, descriptions, routes, and module view exports.

## 1. Decision

The GUI keeps module visibility backend-owned through the platform navigation
contract. The frontend may render a concrete module screen only when the module
id is also registered in the GUI module description map and exported through the
modules barrel.

This prevents a module from becoming partially wired, for example visible in
navigation but missing the route view, or implemented as a route without a
shared module description.

## 2. Active GUI Module Routes

The current active module views are:

```text
assets -> AssetsLibraryView
catalog -> CatalogCoreView
evidence -> EvidenceHubView
integration_mapping -> IntegrationMappingView
load_plan -> LoadPlanView
master_data -> MasterDataView
order_release_generator -> OrderReleaseGeneratorView
rates -> RatesSummaryView
```

Each active module id must have:

```text
- a description in frontend/src/app/routes/moduleDescriptions.ts
- an explicit branch in WorkbenchRoute inside frontend/src/app/App.tsx
- an exported view in frontend/src/modules/index.ts
```

## 3. Placeholder-Only Modules

The following ids may appear in backend navigation as planned, disabled, or
admin-controlled module workspaces, but they do not yet have dedicated GUI
module views:

```text
admin
dev_tools
```

These ids keep shared placeholder behavior until a backend contract and module
view are implemented.

## 4. Guardrail

The contract is enforced by:

```text
frontend/tests/moduleNavigationContract.test.ts
```

When adding a module screen, update the active route list in the test together
with the route, module barrel export, and module description. When keeping a
module placeholder-only, leave it out of explicit App view routing.

## 5. Backend Ownership

This contract does not move business rules to the frontend. Navigation
availability, module status, permission, capability, and lifecycle decisions
remain backend-owned. The frontend contract only protects rendering consistency.
