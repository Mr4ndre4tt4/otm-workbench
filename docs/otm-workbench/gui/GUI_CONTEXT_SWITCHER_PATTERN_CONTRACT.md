# GUI Context Switcher Pattern Contract

**Status:** delivered  
**Branch:** `codex/gui-context-switcher-contract`  
**Scope:** shared shell rendering for active context selection.

## 1. Decision

Active context selection must use the shared `ContextSwitcher` shell component
instead of rendering `context-switcher` forms directly inside route or module
content.

This keeps project, profile, environment, and domain switching consistent while
preserving backend ownership of available context options and update rules.

## 2. Current Contract

Use:

```text
ContextSwitcher
```

For:

```text
- project selection
- profile selection
- environment selection
- domain input
- active context update submission
```

Do not use raw `context-switcher` markup outside:

```text
frontend/src/app/shell/ContextSwitcher.tsx
```

## 3. Boundary

The component owns form rendering and local selection state only.

Backend remains responsible for:

```text
- project/profile/environment option lists
- valid context combinations
- active context persistence
- domain visibility rules
- permission and feature flag decisions
```

The frontend must not infer valid combinations beyond disabling dependent
selectors while backend options are unavailable.

## 4. Guardrail

The contract is enforced by:

```text
frontend/src/app/shell/ContextSwitcher.test.tsx
frontend/tests/contextSwitcherPatternContract.test.ts
```

The static contract blocks raw `context-switcher` markup outside the shared
shell component.

## 5. Next Extensions

Later slices can extend this pattern with:

```text
- backend-provided display names
- domain picker instead of free text
- context presets
- read-only context mode
- optimistic refresh messaging
```

Those extensions should continue using backend-owned active context contracts.
