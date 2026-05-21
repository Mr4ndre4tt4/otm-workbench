# GUI Browser Visual QA OTM-77

**Status:** completed with local Playwright fallback  
**Date:** 2026-05-21  
**Branch:** `codex/gui-foundation-integration-pr-plan`  
**Linear:** `OTM-77`  
**PR:** #181

## 1. Scope

Run a browser-backed visual QA pass for the GUI foundation using synthetic-only
data and a local backend/frontend runtime.

Covered:

```text
- login shell
- Project Cockpit with active synthetic context
- light-to-dark preference update
- compact density preference update
- collapsed sidebar preference update
- desktop viewport: 1280 x 840
- mobile viewport: 390 x 844
- console/runtime smoke
```

## 2. Runtime

The in-app Browser plugin was attempted first. It failed before page inspection
with a closed browser-control transport, so no in-app browser screenshot claim
is made.

Fallback used:

```text
npx --package @playwright/cli playwright-cli
```

Local services:

```text
FastAPI: http://127.0.0.1:8000
Vite:    http://127.0.0.1:5173
```

Important backend setup note: FastAPI must be started with `PYTHONPATH=src`.
Without that, Python may import an older installed package and miss current
routes such as `/api/v1/platform/user-preferences`.

## 3. Synthetic Data

```text
User: synthetic.user@example.test
Workspace: GUI Validation Workspace
Project: GUI Synthetic Rollout
Profile: Default
Environment: DEV
Domain: OTM1
```

No real client names, identifiers, payloads, CNPJ, CPF, or customer screenshots
were used.

## 4. Findings

### Fixed During QA

```text
1. Dark mode contrast regression:
   .app-shell changed tokens but did not apply background/color, so inherited
   browser text color made card content nearly unreadable.

2. Favicon 404:
   Browser console reported /favicon.ico as an error. A simple SVG favicon is
   now linked from index.html.
```

### Not A Product Bug

```text
Initial /api/v1/platform/user-preferences 404 came from starting uvicorn without
PYTHONPATH=src, which loaded an older installed package instead of current branch
source.
```

## 5. Evidence

Local screenshots were captured under `output/playwright/` and intentionally
left out of git:

```text
output/playwright/otm77_home_desktop_dark_compact_collapsed_fixed.png
output/playwright/otm77_home_mobile_dark_compact_collapsed_fixed.png
```

Visual result:

```text
- desktop layout renders without blank screen or major overlap
- mobile layout stacks controls and cards without horizontal overflow
- dark mode text contrast is readable after the shell color/background fix
- compact density and collapsed sidebar state are reflected in DOM and visuals
- final clean console check had only the standard React DevTools info message
```

## 6. Residual Risk

This pass validates the Project Cockpit shell path. Module-specific visual QA
for Rates, Load Plan, Evidence Hub, Assets, Order Release, and Integration
Mapping should be run as separate module slices when their GUI workflows are
actively reviewed.
