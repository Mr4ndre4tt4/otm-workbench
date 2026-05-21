# GUI Button Pattern Contract

**Status:** delivered  
**Branch:** `codex/gui-button-pattern-contract`  
**Scope:** shared frontend rendering for command buttons and icon-only controls.

## 1. Decision

App, shell, and module screens must use shared `Button` and `IconButton`
components instead of raw `<button>` elements or direct button classes.

This keeps command sizing, disabled behavior, variants, accessible labels, and
future icon/theme treatment consistent across the workbench.

## 2. Current Contract

Use:

```text
Button
IconButton
```

For:

```text
- form submission commands
- backend action buttons through ActionBar
- sign out and context commands
- preference/theme/density/sidebar toggles
- compact icon-only commands
```

Raw `<button>` elements are allowed only inside:

```text
frontend/src/ui/components/primitives.tsx
```

Do not use raw `button-primary` or `button-secondary` classes outside the UI
component implementation.

## 3. Boundary

The components own command presentation and accessibility affordances only.

Backend remains responsible for:

```text
- available actions
- disabled state and disabled reason
- permission and lifecycle decisions
- command result hints
- user preferences persisted by backend
```

The frontend must not infer command availability from local UI state when the
backend provides an action contract.

## 4. Guardrail

The contract is enforced by:

```text
frontend/tests/buttonPatternContract.test.ts
frontend/src/ui/components.test.tsx
```

The static contract blocks raw buttons in app/module screens and blocks direct
button variant classes outside shared UI components.

## 5. Next Extensions

Later slices can extend this pattern with:

```text
- icon mapping by backend icon_key
- loading spinner treatment
- destructive/confirmation variants
- tooltip behavior for disabled controls
- dark/light icon variants
```

Those extensions should continue using backend-owned action and preference
contracts.
