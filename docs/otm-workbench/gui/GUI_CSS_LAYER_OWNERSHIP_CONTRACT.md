# GUI CSS Layer Ownership Contract

Date: 2026-05-21
Branch: `codex/gui-css-layer-ownership-contract`

## Objective

Protect the CSS layer boundaries after the GUI stylesheet split, so new modules do not blur component, shell, layout, and preference override responsibilities.

## Delivered

- Added `frontend/tests/cssLayerOwnership.test.ts`.
- The test keeps component primitives out of shell and module layout selectors.
- The test ensures density overrides remain scoped to `.app-shell[data-density="compact"]`.
- The test ensures collapsed sidebar overrides remain scoped to `.app-shell[data-sidebar="collapsed"]`.
- The test ensures responsive overrides stay contained in the mobile breakpoint file.

## Guardrails

- Add reusable primitive styling to `frontend/src/ui/components.css`.
- Add operational page/module layout styling to `frontend/src/ui/layouts.css`.
- Add shell/navigation/topbar styling to `frontend/src/app/shell/shell.css`.
- Add backend-owned preference overrides to the matching token override file.
- Update this contract deliberately if a new CSS layer is introduced.

## Non-goals

- This is not visual QA and does not replace screenshots.
- This does not validate pixel output.
- This does not block intentional architecture changes when the contract is updated with the change.
