# GUI CSS Entrypoint Contract

Date: 2026-05-21
Branch: `codex/gui-css-entrypoint-contract`

## Objective

Turn the CSS layer order into an automated contract so future GUI work keeps the design system modular and predictable.

## Delivered

- Added `frontend/tests/cssArchitecture.test.ts`.
- The test asserts that `frontend/src/styles.css` remains an ordered import-only entrypoint.
- The test asserts that every imported CSS layer exists in its expected ownership path.

## Locked Import Order

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

## Rationale

- Theme tokens must load before all consumers.
- Base styles must load before shell, components, and layouts.
- Shell, component, and layout layers establish the default GUI.
- Density, sidebar, and responsive layers are backend-owned preference/viewport overrides and must load last.

## Guardrails

- Do not add raw CSS rules directly to `styles.css`.
- Add new CSS to the owning layer, or create a new layer and update this contract deliberately.
- Keep browser visual QA separate from this contract; this test verifies structure, not rendered pixels.
