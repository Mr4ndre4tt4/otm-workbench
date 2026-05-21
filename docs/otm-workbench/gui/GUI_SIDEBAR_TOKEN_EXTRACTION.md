# GUI Sidebar Token Extraction

**Status:** delivered  
**Branch:** `codex/gui-sidebar-token-extraction`  
**Scope:** base sidebar collapsed-state CSS extraction; no visual redesign.

## Delivered

Created:

```text
frontend/src/ui/tokens/sidebar.css
```

Moved unchanged from `frontend/src/styles.css`:

```text
.app-shell[data-sidebar="collapsed"]
.app-shell[data-sidebar="collapsed"] .sidebar
.app-shell[data-sidebar="collapsed"] .brand-lockup
.app-shell[data-sidebar="collapsed"] .brand-text
.app-shell[data-sidebar="collapsed"] .nav-label
.app-shell[data-sidebar="collapsed"] .nav-item
```

`frontend/src/styles.css` now imports sidebar tokens after theme and density:

```css
@import "./ui/tokens/theme.css";
@import "./ui/tokens/density.css";
@import "./ui/tokens/sidebar.css";
```

## Guardrails

```text
- No sidebar values changed.
- No selectors changed.
- No backend preference behavior changed.
- No component styling moved beyond base collapsed-sidebar controls.
- Responsive sidebar overrides remain in styles.css to preserve CSS order.
```

## Responsive Note

The `@media` sidebar overrides were intentionally not moved in this slice. Their
order relative to base styles affects mobile behavior. Move them only in a later
responsive-layout extraction where the ordering can be preserved and visually
verified.

## Validation

```text
npm run lint
npm run test
npm run build
```

All passed locally.

## Next Token Slice

The next cleanup can either extract responsive layout rules as a dedicated file
or pause token extraction and start a visual QA pass for light, dark, compact,
and collapsed-sidebar combinations.
