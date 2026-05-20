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
Lucide icons for temporary shell icons
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

The next GUI slice should add a real authenticated API session path and a
contract-safe fallback state for unauthenticated local development, then run
browser visual verification against the local FastAPI backend.
