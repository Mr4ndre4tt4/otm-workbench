# GUI Shared Component Style Extraction

Date: 2026-05-21
Branch: `codex/gui-shared-component-styles`

## Objective

Move reusable component styling out of the shell-level stylesheet without changing the current GUI appearance or backend-owned behavior.

## Delivered

- Created `frontend/src/ui/components.css`.
- Moved shared styles for:
  - `Button`
  - `IconButton`
  - `StatusChip`
  - preference error messages
  - form success/error messages
- Imported the component stylesheet from `frontend/src/styles.css` after the token files.
- Left layout, module panels, shell grid, responsive rules, and token definitions unchanged.

## Guardrails

- No redesign in this slice.
- No new component library.
- No module-specific styling rules moved into the shared component file.
- Backend-owned attributes remain the source of truth for `data-theme`, `data-density`, and `data-sidebar`.

## Follow-up

- Extract shell layout styles into a dedicated shell stylesheet after visual QA remains green.
- Keep `frontend/src/ui/components.css` limited to reusable UI primitives and shared state indicators.
