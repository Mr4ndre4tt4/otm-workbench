# GUI React Boundary Contract

Date: 2026-05-21
Branch: `codex/gui-react-boundary-contract`

## Objective

Protect React ownership boundaries after the GUI shell and module views were split out of `App.tsx`.

## Delivered

- Added `frontend/tests/reactBoundary.test.ts`.
- The test ensures `App.tsx` consumes module views through `../modules`.
- The test ensures `App.tsx` consumes shell components through `./shell`.
- The test verifies expected module view exports remain centralized in `frontend/src/modules/index.ts`.
- The test verifies expected shell exports remain centralized in `frontend/src/app/shell/index.ts`.

## Guardrails

- New module views should be exported from `frontend/src/modules/index.ts`.
- `App.tsx` should not import module views from individual module folders.
- New shell components should be exported from `frontend/src/app/shell/index.ts`.
- `App.tsx` should not import shell components from individual shell files.
- Shared UI primitives still belong under `frontend/src/ui`.

## Non-goals

- This does not validate rendered behavior.
- This does not replace route/module contract tests.
- This does not prevent deliberate architecture changes when the contract is updated with the change.
