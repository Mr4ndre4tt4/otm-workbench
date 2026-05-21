# GUI Rates Visual QA OTM-78

**Status:** completed with local Playwright fallback  
**Date:** 2026-05-21  
**Branch:** `codex/gui-foundation-integration-pr-plan`  
**Linear:** `OTM-78`  
**PR:** #181

## 1. Scope

Run a browser-backed visual and keyboard QA slice for Rates Studio using
synthetic-only data and the current local backend/frontend runtime.

Covered:

```text
- Rates Studio summary metrics
- recent rate batch list
- selected rate object panel
- Validate, Approve, Export CSV, View artifacts, and View evidence actions
- batch artifacts panel
- batch evidence panel
- desktop viewport: 1280 x 840
- mobile viewport: 390 x 844
- keyboard focus smoke
- console/runtime smoke
```

## 2. Runtime

The in-app Browser plugin was not used for this slice because OTM-77 already
recorded the browser-control transport failure. This slice used the same local
fallback:

```text
npx --package @playwright/cli playwright-cli
```

Local services:

```text
FastAPI: http://127.0.0.1:8000
Vite:    http://127.0.0.1:5173
```

FastAPI was started with `PYTHONPATH=src` to ensure the current branch routes
were imported.

## 3. Synthetic Data

```text
User: synthetic.user@example.test
Workspace: Rates QA Workspace
Project: Rates Synthetic Rollout
Profile: Default
Environment: DEV
Domain: OTM1
Rate batch: synthetic accessorial-only export batch
```

No real client names, identifiers, customer payloads, CNPJ, CPF, or customer
screenshots were used.

## 4. Findings

### Fixed During QA

```text
1. Selected-object action buttons could wrap labels letter-by-letter on narrow
   containers. Button text now keeps normal word wrapping and detail actions use
   a stable responsive grid.

2. Artifact and evidence rows could overflow or force status chips into vertical
   text when panels were displayed side by side. Artifact rows now separate main
   text, metadata, and action/status areas with responsive grid areas.

3. Mobile table rows were too constrained by the status column. Responsive table
   rows now give the object title enough space before moving the status chip.
```

## 5. Evidence

Local screenshots were captured under `output/playwright/` and intentionally
left out of git:

```text
output/playwright/otm78_rates_desktop_final.png
output/playwright/otm78_rates_mobile_final3.png
```

Visual result:

```text
- desktop Rates layout renders without overlap or clipped action controls
- mobile Rates layout stacks shell controls, metrics, selected object, artifacts,
  and evidence without horizontal overflow
- status chips remain single-line in artifact and evidence rows
- long artifact names wrap inside their card instead of pushing controls outside
- final clean console check had only the standard React DevTools info message
```

Keyboard smoke:

```text
Focus reached theme controls, create batch, recent batch row, Validate, Approve,
Export CSV, View artifacts, View evidence, Download, and sidebar navigation.
```

## 6. Residual Risk

This pass validates the rendered Rates Studio summary and current happy-path
export evidence state. It does not replace later accessibility QA, empty/error
state review, or a full keyboard interaction pass for modal/dialog flows when
those flows are added.
