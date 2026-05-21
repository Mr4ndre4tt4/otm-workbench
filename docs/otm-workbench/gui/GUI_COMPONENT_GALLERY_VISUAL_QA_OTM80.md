# GUI Component Gallery Visual QA OTM-80

**Status:** completed with local Playwright fallback  
**Date:** 2026-05-21  
**Branch:** `codex/gui-foundation-integration-pr-plan`  
**Linear:** `OTM-80`  
**PR:** #181

## 1. Scope

Run a browser-backed visual and keyboard QA slice for the internal component
gallery route using synthetic-only data and the current local backend/frontend
runtime.

Target route:

```text
/__gui/component-gallery
```

Covered:

```text
- MetricGrid examples
- WorkbenchShell preview
- LoginPanel preview
- ContextSummary and ContextSwitcher preview
- PreferenceControls light, dark, density, and sidebar controls
- ActionBar enabled, disabled, and running states
- StatusChip variants
- ModuleObjectList, SelectedObjectPanel, and DetailList examples
- ArtifactList rows and command placement
- FeedbackMessage and StatePanel examples
- BlockerPanel example
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
Project: Project QA
Profile: Default
Environment: DEV
Domain: SYN_DOMAIN
Objects: synthetic ready, blocked, artifact, and blocker fixtures
```

No real client names, identifiers, customer payloads, CNPJ, CPF, or customer
screenshots were used.

## 4. Findings

### Fixed During QA

```text
1. LoginPanel was rendered inside a narrow gallery panel while preserving the
   production two-column login layout. The gallery preview compressed the
   heading, body, and form controls.

2. The gallery now scopes a single-column LoginPanel preview to
   gallery-auth-preview. The production LoginPanel pattern remains unchanged.

3. The ContextSwitcher preview used fixed columns plus long synthetic visible
   values. The gallery-selector-preview now uses responsive columns and shorter
   synthetic display labels so desktop and mobile previews stay readable.

4. The gallery icon command example inherited full-width detail action rules
   and produced a poor mobile example. It now uses gallery-command-preview so
   the icon button and command buttons keep stable, intentional sizing.
```

## 5. Evidence

Local screenshots were captured under `output/playwright/` and intentionally
left out of git:

```text
output/playwright/otm80_gallery_desktop_final.png
output/playwright/otm80_gallery_mobile_final.png
```

Visual result:

```text
- desktop gallery renders without clipped panel controls or LoginPanel overlap
- mobile gallery stacks shell, metrics, panels, workspace, artifacts, states,
  and blockers without horizontal overflow
- ContextSwitcher preview labels and values fit in both desktop and mobile
- StatusChip values remain readable and wrap by row instead of clipping
- ActionBar and gallery command examples retain professional button sizing
- final console check had zero errors and zero warnings, with only the standard
  React DevTools info message
```

Keyboard smoke:

```text
Focus reached sidebar navigation, Sign out, theme/density/sidebar preference
controls, header actions, LoginPanel inputs, object list rows, and selected
gallery commands. The visible black outline in the desktop screenshot is the
expected keyboard focus indicator.
```

## 6. Residual Risk

This pass validates the internal component gallery route, not a production
Storybook replacement. Future reusable components should add gallery examples,
contract tests, and visual QA evidence before being adopted by module screens.

This pass does not replace later accessibility QA for dialogs, editable forms,
drag/drop flows, tables with inline editing, or custom mapping canvas behavior.
