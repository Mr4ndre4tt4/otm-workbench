# GUI Base Style Extraction

Date: 2026-05-21
Branch: `codex/gui-base-style-extraction`

## Objective

Make `frontend/src/styles.css` a CSS entrypoint only, with global reset and base typography owned by a dedicated file.

## Delivered

- Created `frontend/src/ui/base.css`.
- Moved global reset and base typography:
  - universal `box-sizing`
  - body background/text color
  - inherited form control fonts
  - base heading and paragraph margins
  - base `h1` and `h2` sizing
- Reduced `frontend/src/styles.css` to ordered stylesheet imports only.

## CSS Entrypoint Order

```css
@import "./ui/tokens/theme.css";
@import "./ui/base.css";
@import "./app/shell/shell.css";
@import "./ui/components.css";
@import "./ui/layouts.css";
@import "./ui/tokens/density.css";
@import "./ui/tokens/sidebar.css";
@import "./ui/tokens/responsive.css";
```

## Guardrails

- No visual values were intentionally changed.
- Theme tokens still load before all CSS that consumes them.
- Base styles load before shell, component, layout, preference, and responsive layers.
- `frontend/src/styles.css` remains the single app stylesheet imported by React.

## Follow-up

- Keep future CSS additions out of `styles.css`; add them to the owning layer.
- Do browser-backed visual QA before further CSS family splits.
