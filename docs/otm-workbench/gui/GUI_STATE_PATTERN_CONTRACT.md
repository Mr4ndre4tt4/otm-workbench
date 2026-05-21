# GUI State Pattern Contract

**Status:** delivered  
**Branch:** `codex/gui-state-pattern-contract`  
**Scope:** shared frontend state rendering for loading, unavailable, and future blocked/empty state patterns.

## 1. Decision

Module screens should use shared UI kit components for operational states
instead of recreating state markup inside each module.

This slice introduces `StatePanel` as the shared loading/unavailable state
surface. The pattern keeps visual tone, icon treatment, spacing, and future
accessibility changes centralized.

## 2. Current Contract

Use:

```text
StatePanel
```

For:

```text
- top-level loading states
- top-level API unavailable states
- unknown backend route state
```

Do not create raw `className="state-panel"` markup in module or app screens.
Raw state-panel markup is owned by:

```text
frontend/src/ui/components.tsx
```

## 3. Boundary

The shared component owns rendering only. It does not own business rules.

Backend remains responsible for:

```text
- whether a module is visible
- whether a route is permitted
- whether a module is disabled or blocked
- status, lifecycle, and capability explanations
```

The GUI only maps backend state to consistent visual surfaces.

## 4. Guardrail

The contract is enforced by:

```text
frontend/tests/statePatternContract.test.ts
frontend/src/ui/components.test.tsx
```

The static contract blocks new raw `state-panel` markup outside the UI kit.
The component test verifies default and error rendering through `StatePanel`.

## 5. Next Extensions

Later slices can extend this same pattern with explicit variants for:

```text
- empty
- no results
- blocked
- read-only
- disabled by permission
- warning
- success
```

Those variants should still consume backend-owned reason/action data.
