# GUI Layout Style Extraction

Date: 2026-05-21
Branch: `codex/gui-layout-style-extraction`

## Objective

Move reusable operational page and module layout styles out of `frontend/src/styles.css` without changing the GUI appearance.

## Delivered

- Created `frontend/src/ui/layouts.css`.
- Moved shared layout styles for:
  - context summary and context switcher
  - readiness banner
  - metric grid and metric cards
  - operational panels
  - module template layouts
  - module rows, detail grids, table lists, artifact lists, and blocker panels
  - loading/error state panels
  - login panel and login form
- Imported `layouts.css` after `components.css` and before density/sidebar/responsive overrides.

## Import Order

```css
@import "./ui/tokens/theme.css";
@import "./app/shell/shell.css";
@import "./ui/components.css";
@import "./ui/layouts.css";
@import "./ui/tokens/density.css";
@import "./ui/tokens/sidebar.css";
@import "./ui/tokens/responsive.css";
```

## Guardrails

- No visual values were intentionally changed.
- No module-specific React code was changed.
- Density and responsive override files still load after base layout styles.
- `frontend/src/styles.css` now remains focused on global reset and base typography.

## Follow-up

- Consider splitting large layout families only after browser-backed QA is available.
- Keep future module screens on these shared layout primitives unless an exception is documented.
