# GUI Integration Mapping Visual QA OTM-79

**Status:** completed with local Playwright fallback  
**Date:** 2026-05-21  
**Branch:** `codex/gui-foundation-integration-pr-plan`  
**Linear:** `OTM-79`  
**PR:** #181

## 1. Scope

Run a browser-backed visual and keyboard QA slice for Integration Mapping Studio
using synthetic-only data and the current local backend/frontend runtime.

Covered:

```text
- Integration Mapping Studio metrics
- definition list
- selected definition detail panel
- payload artifact rows
- schema document rows
- mapping rows with XML and JSON path-like labels
- desktop viewport: 1280 x 840
- mobile viewport: 390 x 844
- keyboard focus smoke
- console/runtime smoke
```

## 2. Runtime

The in-app Browser plugin remains unavailable in this Codex session, so this
slice used the accepted local fallback:

```text
npx --package @playwright/cli playwright-cli
```

Local services:

```text
FastAPI: http://127.0.0.1:8000
Vite:    http://127.0.0.1:5173
```

FastAPI was started with `PYTHONPATH=src` and an isolated SQLite database for
this QA slice.

## 3. Synthetic Data

```text
User: synthetic.user@example.test
Workspace: Integration QA Workspace
Project: Integration Synthetic Rollout
Profile: Default
Environment: DEV
Domain: OTM1
Definition: synthetic XML to JSON mapping definition
Payloads: synthetic XML source and JSON target samples
```

No real client names, identifiers, customer payloads, CNPJ, CPF, or customer
screenshots were used.

## 4. Findings

### Fixed During QA

```text
1. DetailList used fixed columns for an arbitrary number of metadata values.
   Integration Mapping rows with payload roles, formats, sizes, content types,
   and XML/JSON paths were squeezed and wrapped poorly.

2. DetailList now separates title, metadata, and status into responsive grid
   areas. Metadata wraps as a flexible row on desktop and stacks on mobile.
```

## 5. Evidence

Local screenshots were captured under `output/playwright/` and intentionally
left out of git:

```text
output/playwright/otm79_integration_desktop_fixed.png
output/playwright/otm79_integration_mobile_fixed.png
```

Visual result:

```text
- desktop Integration Mapping layout renders without clipped controls or panel
  overflow
- mobile layout stacks metrics, definition list, selected definition, payloads,
  schemas, and mappings without horizontal overflow
- payload file names and path-like mapping labels wrap inside their cards
- status chips remain readable and single-line
- final clean console check had only the standard React DevTools info message
```

Keyboard smoke:

```text
Focus reached sidebar navigation, Sign out, theme/density/sidebar preference
controls, and the selected Integration Mapping definition row.
```

## 6. Residual Risk

This pass validates the current read-only Integration Mapping Studio view. It
does not replace later accessibility QA for future editable mapping actions,
schema tree expansion, preview jobs, dialogs, or custom canvas/table flows when
those workflows are added.
