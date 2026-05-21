# GUI QA Accessibility Pass Completion Review OTM-60

**Status:** completed for current GUI foundation  
**Date:** 2026-05-21  
**Branch:** `codex/gui-foundation-integration-pr-plan`  
**Linear:** `OTM-60`  
**PR:** #181

## 1. Purpose

Close the current GUI visual QA and accessibility pass for the MVP1 GUI
foundation.

This review records the browser-backed evidence, keyboard smoke coverage,
console checks, responsive fixes, and recurring QA matrix that now govern future
GUI module work.

## 2. Completed Evidence

Current evidence files:

```text
OTM-77: GUI_BROWSER_VISUAL_QA_OTM77.md
OTM-78: GUI_RATES_VISUAL_QA_OTM78.md
OTM-79: GUI_INTEGRATION_MAPPING_VISUAL_QA_OTM79.md
OTM-80: GUI_COMPONENT_GALLERY_VISUAL_QA_OTM80.md
OTM-81: GUI_ACCESSIBILITY_QA_MATRIX.md
OTM-82: GUI_RATES_MVP_COMPLETION_REVIEW_OTM58.md
OTM-83: GUI_SHARED_OPERATIONAL_PANELS_COMPLETION_REVIEW_OTM59.md
```

These files cover visual QA evidence, recurring QA expectations, and completion
reviews for the GUI slices that were active in this cycle.

## 3. Covered Routes And Areas

The current pass covered:

```text
- login shell
- Project Cockpit with synthetic active context
- light, dark, compact, and collapsed sidebar preference states
- Rates Studio summary, detail, actions, artifacts, and evidence
- Integration Mapping Studio read-only mapping surface
- internal component gallery
- shared operational panels for jobs, artifacts, evidence, blockers, and
  activity rows
```

The accepted baseline for future slices is now defined in:

```text
GUI_ACCESSIBILITY_QA_MATRIX.md
```

## 4. Browser Runtime Boundary

The in-app Browser plugin remains unavailable in this Windows sandbox because
the browser-control transport failed before reliable page inspection.

The accepted local fallback for this cycle was:

```text
npx --package @playwright/cli playwright-cli
```

No in-app Browser screenshot claim is made for this pass. The completed visual
evidence uses local Playwright fallback screenshots and console/keyboard smoke
checks.

## 5. Viewports And Runtime Checks

The visual QA slices used:

```text
Desktop: 1280 x 840
Mobile:  390 x 844
```

Runtime checks included:

```text
- route load checks against local FastAPI and Vite
- console smoke with zero errors and zero warnings after fixes
- standard React DevTools informational message accepted in local dev
- screenshots stored under output/playwright/ and intentionally left out of git
```

## 6. Keyboard And Accessibility Coverage

Keyboard smoke covered the current interactive surfaces:

```text
- sidebar navigation links
- Sign out
- theme, density, and sidebar preference controls
- page header actions
- context and login inputs where present
- Rates object rows and backend actions
- artifact download action
- Integration Mapping definition row
- component gallery object rows and command examples
```

The current component contracts also require:

```text
- accessible labels for OperationalPanel usage
- icon-only labels and titles
- shared row/list/panel components instead of raw module-local markup
- visible keyboard focus indicators
- backend-owned disabled reasons and statuses where available
```

## 7. Fixed During QA Cycle

The QA cycle fixed:

```text
- dark mode contrast regression in the app shell
- local favicon 404 console error
- Rates action button wrapping in narrow containers
- Rates artifact/evidence row overflow
- mobile table row status-column constraints
- Integration Mapping DetailList metadata wrapping
- component gallery LoginPanel preview compression
- component gallery ContextSwitcher responsive columns and synthetic labels
- component gallery command preview sizing on mobile
```

## 8. Client Data Guardrail

This QA pass used synthetic data only.

Do not capture or commit:

```text
- real client names
- customer identifiers
- payload values
- local customer paths
- screenshots from customer data
- CNPJ or CPF values
- secrets
```

## 9. Residual Risk

OTM-60 is complete for the current GUI foundation and active read-oriented
module surfaces.

Future work should create separate issues for:

```text
- dialogs and confirmation flows
- editable forms
- tables with inline editing
- drag/drop or mapping canvas interactions
- schema tree expansion
- import/export job progress surfaces
- richer no-results/error permutations
- assistive technology testing beyond keyboard smoke
- module-specific visual QA when new surfaces are added
```

Those future slices should use `GUI_ACCESSIBILITY_QA_MATRIX.md` as the baseline
and should add route-specific evidence before marking their GUI scope complete.
