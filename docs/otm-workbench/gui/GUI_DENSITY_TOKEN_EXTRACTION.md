# GUI Density Token Extraction

**Status:** delivered  
**Branch:** `codex/gui-density-token-extraction`  
**Scope:** density CSS extraction; no visual redesign.

## Delivered

Created:

```text
frontend/src/ui/tokens/density.css
```

Moved unchanged from `frontend/src/styles.css`:

```text
.app-shell[data-density="compact"]
.app-shell[data-density="compact"] .main-area
.app-shell[data-density="compact"] .readiness
.app-shell[data-density="compact"] .metric
.app-shell[data-density="compact"] .panel
.app-shell[data-density="compact"] .module-template-main
.app-shell[data-density="compact"] .module-template-side
.app-shell[data-density="compact"] .activity-row
.app-shell[data-density="compact"] .module-row
.app-shell[data-density="compact"] .context-switcher
```

`frontend/src/styles.css` now imports density tokens after theme tokens:

```css
@import "./ui/tokens/theme.css";
@import "./ui/tokens/density.css";
```

## Guardrails

```text
- No spacing values changed.
- No selectors changed.
- No backend preference behavior changed.
- No component styling moved beyond compact density overrides.
- No sidebar layout styling moved in this slice.
```

## Validation

```text
npm run lint
npm run test
npm run build
```

All passed locally.

## Next Token Slice

The next CSS cleanup can extract sidebar layout controls into a dedicated file,
again keeping selectors and values unchanged.
