# GUI CSS Token Audit

**Status:** delivered  
**Branch:** `codex/gui-platform-types-cleanup`  
**Scope:** audit only; no visual redesign or CSS extraction in this slice.

## Purpose

Review the current GUI CSS/token shape before splitting `frontend/src/styles.css`
into token, theme, layout, and component style files.

The goal is to preserve the current operational look while making the design
system easier to evolve consistently across modules.

## Current State

The GUI currently keeps the full shell and component stylesheet in:

```text
frontend/src/styles.css
```

The file already has a useful first token layer:

```text
--bg
--surface
--surface-subtle
--text
--muted
--border
--accent
--accent-strong
--success
--warning
--danger
--shadow
```

Theme switching is handled through:

```text
:root
.app-shell[data-theme="dark"]
@media (prefers-color-scheme: dark) {
  .app-shell[data-theme="system"]
}
```

Density and sidebar preferences are also applied through root shell attributes:

```text
.app-shell[data-density="compact"]
.app-shell[data-sidebar="collapsed"]
```

This matches the backend-owned preference contract and should be preserved.

## Strengths

```text
- Light mode is default.
- Dark mode uses explicit values instead of automatic inversion.
- System theme follows OS preference through CSS media query.
- Density and sidebar mode are controlled by backend-owned preferences.
- Most colors already flow through variables.
- Component styles are compact and operational, not decorative.
- Border radius is consistently restrained at 8px for panels/buttons.
```

## Risks

```text
- Token names are short and implementation-oriented, not semantic enough.
- Status tokens and action tokens are mixed with general color tokens.
- Layout, shell, component, and state styles live in one large file.
- Density overrides are spread through component selectors.
- Shadows are part of theme/density but not named by role.
- White is still used directly for primary button text.
- Future module-specific widgets may start adding raw colors unless token rules are explicit.
```

## Recommended Token Direction

Move toward semantic token groups without changing current colors:

```text
color.background.app
color.background.surface
color.background.subtle
color.text.primary
color.text.muted
color.border.default
color.action.primary
color.action.primaryHover
color.status.success
color.status.warning
color.status.danger
shadow.panel
radius.control
radius.panel
space.*
font.*
```

CSS variable naming can stay CSS-friendly:

```text
--color-background-app
--color-background-surface
--color-background-subtle
--color-text-primary
--color-text-muted
--color-border-default
--color-action-primary
--color-action-primary-hover
--color-status-success
--color-status-warning
--color-status-danger
--shadow-panel
--radius-control
--radius-panel
```

## Suggested File Split

Keep the split conservative:

```text
frontend/src/ui/tokens/theme.css
  light, dark, and system theme variables

frontend/src/ui/tokens/density.css
  comfortable and compact density overrides

frontend/src/ui/tokens/layout.css
  app shell sizing, sidebar width, page spacing

frontend/src/ui/tokens/index.css
  imports the token files

frontend/src/styles.css
  imports tokens first, then keeps existing component styles
```

Only after this is stable should component-specific style files be considered.

## Extraction Guardrails

```text
- Do not change colors, spacing, or behavior in the first token extraction.
- Preserve data-theme, data-density, and data-sidebar selectors.
- Keep backend-owned preferences as the source of root shell attributes.
- Do not introduce Tailwind, shadcn, or a new styling framework in this slice.
- Do not add module-specific palettes.
- Do not add decorative gradients, orbs, or landing-page treatments.
- Run visual/browser verification when a future slice changes CSS behavior.
```

## Candidate First Extraction

The next implementation slice should be:

```text
1. Create frontend/src/ui/tokens/theme.css.
2. Move :root, dark, and system theme variable blocks unchanged.
3. Import theme.css from styles.css.
4. Run npm run lint, npm run test, npm run build.
5. If browser tooling is available, verify light, dark, and system theme controls.
```

That first extraction is intentionally small. Density/layout extraction should
follow only after theme extraction is verified.

## First Extraction Result

The first extraction was completed in `GUI_THEME_TOKEN_EXTRACTION.md`.

Delivered:

```text
frontend/src/ui/tokens/theme.css
```

The moved theme blocks were kept unchanged.

The second extraction was completed in `GUI_DENSITY_TOKEN_EXTRACTION.md`.

Delivered:

```text
frontend/src/ui/tokens/density.css
```

The moved compact-density blocks were kept unchanged.

The third extraction was completed in `GUI_SIDEBAR_TOKEN_EXTRACTION.md`.

Delivered:

```text
frontend/src/ui/tokens/sidebar.css
```

Only base collapsed-sidebar blocks were moved. Responsive sidebar overrides
remain in `styles.css` to preserve CSS order until a dedicated responsive
layout extraction is planned.

The responsive layout extraction was completed in
`GUI_RESPONSIVE_TOKEN_EXTRACTION.md`.

Delivered:

```text
frontend/src/ui/tokens/responsive.css
```

The full `@media (max-width: 900px)` block was moved unchanged and imported
after theme, density, and sidebar token files.

## Shell QA Contracts

The shell QA contract slice was completed in `GUI_SHELL_QA_CONTRACTS.md`.

Delivered:

```text
frontend/src/app/shell/SidebarNav.test.tsx
frontend/src/app/App.test.tsx
```

The tests cover backend-owned system theme persistence, shell data attributes,
and expanded versus collapsed navigation behavior.

## Shared Component Style Extraction

The shared component style extraction was completed in
`GUI_SHARED_COMPONENT_STYLE_EXTRACTION.md`.

Delivered:

```text
frontend/src/ui/components.css
```

The file owns reusable primitive styles for buttons, icon buttons, status chips,
and shared form/preference messages. Shell layout and module-specific styles
remain in `frontend/src/styles.css`.

## Shell Style Extraction

The shell style extraction was completed in `GUI_SHELL_STYLE_EXTRACTION.md`.

Delivered:

```text
frontend/src/app/shell/shell.css
```

Base shell, sidebar navigation, topbar, preference/action layout, page header,
and section label styles now live with shell components. Preference and
responsive override files load after the base shell stylesheet.

## Layout Style Extraction

The layout style extraction was completed in
`GUI_LAYOUT_STYLE_EXTRACTION.md`.

Delivered:

```text
frontend/src/ui/layouts.css
```

Shared operational page and module layout styles now live in `layouts.css`.
`frontend/src/styles.css` is reduced to global reset and base typography.

## Base Style Extraction

The base style extraction was completed in
`GUI_BASE_STYLE_EXTRACTION.md`.

Delivered:

```text
frontend/src/ui/base.css
```

Global reset and base typography now live in `base.css`. `frontend/src/styles.css`
is an ordered CSS entrypoint only.

## Browser QA Attempt

The browser QA attempt was recorded in `GUI_BROWSER_QA_ATTEMPT.md`.

The local Vite server responded with HTTP 200 at `http://127.0.0.1:5173/`, but
the in-app browser runner was blocked by the Windows process creation
environment. No browser screenshot evidence is claimed for the CSS split yet.

## CSS Entrypoint Contract

The CSS entrypoint contract was completed in
`GUI_CSS_ENTRYPOINT_CONTRACT.md`.

Delivered:

```text
frontend/tests/cssArchitecture.test.ts
```

The test locks `frontend/src/styles.css` as an import-only entrypoint and checks
that all imported CSS ownership layers exist.

## CSS Layer Ownership Contract

The CSS layer ownership contract was completed in
`GUI_CSS_LAYER_OWNERSHIP_CONTRACT.md`.

Delivered:

```text
frontend/tests/cssLayerOwnership.test.ts
```

The test protects component, density, sidebar, and responsive layer boundaries
so future modules do not mix CSS responsibilities casually.

## React Boundary Contract

The React boundary contract was completed in
`GUI_REACT_BOUNDARY_CONTRACT.md`.

Delivered:

```text
frontend/tests/reactBoundary.test.ts
```

The test protects App/module/shell barrel boundaries so new GUI modules keep
the same ownership model.

## Acceptance Criteria

The CSS token audit is accepted when:

```text
- current token strengths and risks are clear
- no visual redesign is bundled into the plan
- semantic token direction is explicit
- first extraction slice is small and reversible
- backend-owned theme preferences remain protected
```
