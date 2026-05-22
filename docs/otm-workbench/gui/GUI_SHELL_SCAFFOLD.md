# GUI Shell Scaffold

**Status:** initial scaffold delivered  
**Branch:** `codex/gui-shell-scaffold`  
**Frontend path:** `frontend/`

## Objective

Create the first browser-first, desktop-ready GUI foundation for OTM Workbench.

This slice intentionally focuses on shell architecture and contract
consumption, not full visual polish or module-specific screens.

## Stack

```text
React
TypeScript
Vite
React Router
TanStack Query
Vitest
Testing Library
ESLint
Lucide icons as temporary fallback renderers until backend-owned icon registry
metadata is implemented
```

The product component boundary is `src/ui/`. Future module screens should use
Workbench UI Kit components from that layer instead of raw third-party UI
primitives.

## Implemented

- `frontend/package.json` with dev, build, test, lint scripts.
- Vite React TypeScript configuration.
- API client helper for backend error envelopes.
- TanStack Query hooks for:
  - `/api/v1/platform/navigation`;
  - `/api/v1/platform/project-cockpit/summary`;
  - `/api/v1/platform/user-preferences`.
- Initial `WorkbenchShell` composition in `App.tsx`.
- Sidebar driven by backend navigation items.
- Project Cockpit panel driven by backend summary contract.
- Minimal UI Kit primitives:
  - `Button`;
  - `IconButton`;
  - `StatusChip`.
- Light-mode design tokens and responsive shell CSS.
- Shell smoke test.

## Backend Ownership Rules

The frontend does not own:

- module visibility;
- active project/profile/environment/domain;
- setup readiness;
- job status;
- artifact/evidence safety;
- user theme preference.
- navigation icon identity and module display labels.

Those values are read from backend contracts and rendered as UI state.

## Desktop-Ready Boundary

The scaffold keeps browser-specific calls inside framework/API boundaries.
Future desktop behavior should be introduced through platform adapters, not by
calling desktop APIs directly inside module screens.

## Verification

```text
npm run build
npm run test
npm run lint
```

All three checks passed after dependency installation.

## Next Step

The shell frame is now centralized in
`frontend/src/app/shell/WorkbenchShell.tsx`, keeping brand, sidebar, topbar,
sign out placement, preference controls, and route content slot out of
module-specific views.

Future shell changes should update `GUI_WORKBENCH_SHELL_PATTERN_CONTRACT.md`
and its tests before expanding visual behavior.

Icon and label metadata should follow
`GUI_BACKEND_OWNED_ICON_ASSET_REGISTRY.md`: the backend owns module labels,
icon keys, icon family/variant references, and navigation ordering; the
frontend only renders approved icons and accessible labels from the returned
contract.
