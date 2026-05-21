# GUI Theme Token Extraction

**Status:** delivered  
**Branch:** `codex/gui-theme-token-extraction`  
**Scope:** first CSS token extraction; no visual redesign.

## Delivered

Created:

```text
frontend/src/ui/tokens/theme.css
```

Moved unchanged from `frontend/src/styles.css`:

```text
:root
.app-shell[data-theme="dark"]
@media (prefers-color-scheme: dark) {
  .app-shell[data-theme="system"]
}
```

`frontend/src/styles.css` now imports theme tokens first:

```css
@import "./ui/tokens/theme.css";
```

## Guardrails

```text
- No color values changed.
- No selectors changed.
- No backend preference behavior changed.
- No component styling moved in this slice.
- No density or sidebar styling moved in this slice.
```

## Validation

```text
npm run lint
npm run test
npm run build
```

All passed locally.

## Next Token Slice

After review, the next CSS cleanup can extract density/layout concerns into a
separate token file. Keep it mechanical and avoid visual redesign.
