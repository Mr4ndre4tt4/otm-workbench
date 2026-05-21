# GUI Shell Style Extraction

Date: 2026-05-21
Branch: `codex/gui-shell-style-extraction`

## Objective

Move the reusable shell and navigation layout styles out of `frontend/src/styles.css` while preserving the backend-owned GUI contracts.

## Delivered

- Created `frontend/src/app/shell/shell.css`.
- Moved base shell styles for:
  - `.app-shell`
  - `.sidebar`
  - brand lockup
  - sidebar navigation
  - topbar
  - preference/action control layout
  - page header and section label
- Reordered stylesheet imports so base shell/component styles load before density, sidebar, and responsive overrides.

## Import Order

```css
@import "./ui/tokens/theme.css";
@import "./app/shell/shell.css";
@import "./ui/components.css";
@import "./ui/tokens/density.css";
@import "./ui/tokens/sidebar.css";
@import "./ui/tokens/responsive.css";
```

This keeps theme tokens first, then base UI, then backend-owned preference and responsive overrides.

## Guardrails

- No visual values were intentionally changed.
- No module-specific panel/list styles were moved in this slice.
- `data-theme`, `data-density`, and `data-sidebar` remain the root shell contracts.
- The file lives next to shell components so future shell changes have an obvious ownership boundary.

## Follow-up

- Extract page/module layout styles only after shell visual QA remains green.
- Add browser-backed screenshots for desktop and mobile once the local browser runner is stable.
