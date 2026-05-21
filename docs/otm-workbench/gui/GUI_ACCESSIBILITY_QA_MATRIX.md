# GUI Accessibility QA Matrix

**Status:** active baseline  
**Date:** 2026-05-21  
**Scope:** recurring accessibility, keyboard, responsiveness, and visual QA
matrix for GUI module work.

## 1. Purpose

This matrix turns GUI visual QA from one-off screenshots into a repeatable
review gate for new module screens and shared components.

It does not replace deeper assistive technology testing. It defines the minimum
baseline every GUI slice must satisfy before it is accepted into the shared
Workbench experience.

## 2. Routes In Baseline

```text
/login
/
/rates
/catalog
/assets
/load-plan
/master-data
/order-release-generator
/integration-mapping
/__gui/component-gallery
```

Routes that are placeholders still need shell, navigation, empty-state, and
preference coverage because they exercise shared GUI behavior.

## 3. Required Viewports

```text
Desktop: 1280 x 840
Mobile:  390 x 844
```

Optional deeper checks:

```text
- 1440 x 900 for dense operational screens
- 1024 x 768 for constrained laptop review
- 320 x 720 only when a route has high mobile risk
```

## 4. Required Preference States

Each route or representative route family must be reviewed with:

```text
- light mode, comfortable density, expanded sidebar
- dark mode, comfortable density, expanded sidebar
- system mode persisted by backend preference contract
- compact density
- collapsed sidebar
```

Preferences remain backend-owned through `/api/v1/platform/user-preferences`.
The GUI may render current preference state, but it must not create durable
frontend-only preference state.

## 5. Keyboard Baseline

Keyboard smoke must confirm focus reaches:

```text
- sidebar navigation links
- Sign out
- theme, density, and sidebar preference controls
- page header primary and secondary actions
- context switcher controls when present
- object list rows when present
- selected object actions when present
- artifact download actions when present
- form fields and submit buttons when present
```

Visible focus indicators are expected and should not be hidden to make
screenshots look cleaner.

## 6. Accessibility Baseline

Every touched slice must confirm:

```text
- buttons and icon buttons have accessible names
- icon-only commands expose labels through aria-label and title
- interactive rows expose selected/pressed state where applicable
- lists, forms, panels, and workspaces have useful aria labels
- disabled actions expose backend-owned disabled reasons when available
- loading, empty, error, blocked, read-only, and success states are reachable
- status chips do not communicate meaning by color alone
- text remains readable in light and dark modes
```

## 7. Responsive Baseline

Every touched slice must confirm:

```text
- no horizontal page overflow at required mobile width
- long labels wrap inside their cards, rows, or controls
- buttons do not shrink below readable command text
- status chips stay readable and do not overlap nearby content
- forms stack predictably on mobile
- module workspace side panels stack under primary content on mobile
- page header actions wrap without covering title or supporting text
```

## 8. Console And Runtime Baseline

Browser-backed QA must include:

```text
- route loads without HTTP/runtime failures
- console has zero errors
- console has zero warnings
- React DevTools informational message is acceptable in local dev
```

## 9. Client Data Rule

GUI QA evidence must use synthetic data only.

Do not capture or commit real client names, identifiers, local customer paths,
payload values, documents, screenshots, CNPJ, CPF, secrets, or production-like
customer references.

## 10. Current Evidence Map

```text
OTM-77: GUI_BROWSER_VISUAL_QA_OTM77.md
OTM-78: GUI_RATES_VISUAL_QA_OTM78.md
OTM-79: GUI_INTEGRATION_MAPPING_VISUAL_QA_OTM79.md
OTM-80: GUI_COMPONENT_GALLERY_VISUAL_QA_OTM80.md
```

These evidence files used the accepted local Playwright fallback because the
in-app Browser plugin was unavailable in the Windows sandbox.

## 11. Acceptance For Future GUI Slices

A future GUI slice is accepted only when it records:

```text
- route or component scope
- backend contracts consumed or explicitly missing
- synthetic data source
- desktop and mobile viewport result
- keyboard smoke result
- console/runtime result
- fixed findings, if any
- residual risk
- Linear issue reference
```

If browser automation is blocked, the slice must record the attempted command,
failure mode, and remaining risk instead of claiming visual QA passed.
