# GUI Context Summary Pattern Contract

**Status:** delivered  
**Branch:** `codex/gui-context-summary-contract`  
**Scope:** shared shell rendering for active project/profile/environment/domain context.

## 1. Decision

Active context summary must use the shared `ContextSummary` shell component
instead of rendering `context-summary` markup directly inside route or module
content.

This keeps project, profile, environment, and domain markers consistent while
preserving backend ownership of active context state.

## 2. Current Contract

Use:

```text
ContextSummary
```

For:

```text
- active project context
- active profile context
- active environment context
- active domain display
```

Do not use raw `context-summary` markup outside:

```text
frontend/src/app/shell/ContextSummary.tsx
```

## 3. Boundary

The component owns context summary presentation only.

Backend remains responsible for:

```text
- active context values
- allowed project/profile/environment options
- context switching rules
- permission and visibility decisions
- domain selection and defaults
```

The frontend must not infer context validity beyond rendering backend-provided
active context values.

## 4. Guardrail

The contract is enforced by:

```text
frontend/src/app/shell/ContextSummary.test.tsx
frontend/tests/contextSummaryPatternContract.test.ts
```

The static contract blocks raw `context-summary` markup outside the shared shell
component.

## 5. Next Extensions

Later slices can extend this pattern with:

```text
- backend-provided context display names
- domain badges
- read-only environment indicators
- warning state for incomplete context
- compact shell variants
```

Those extensions should continue using backend-owned active context contracts.
