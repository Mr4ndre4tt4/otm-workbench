# GUI Readiness Panel Pattern Contract

**Status:** delivered  
**Branch:** `codex/gui-readiness-panel-contract`  
**Scope:** shared frontend rendering for cockpit project context readiness.

## 1. Decision

Project context readiness must use the shared `ReadinessPanel` shell component
instead of rendering `readiness` markup directly inside route content.

This keeps the cockpit readiness state consistent while preserving backend
ownership of active context and setup status.

## 2. Current Contract

Use:

```text
ReadinessPanel
```

For:

```text
- Project Cockpit context readiness
- active project/profile/environment guidance
- setup status counts
```

Do not use raw `readiness` or `readiness-ready` markup outside:

```text
frontend/src/app/shell/ReadinessPanel.tsx
```

## 3. Boundary

The component owns readiness presentation only.

Backend remains responsible for:

```text
- active context status
- profile/environment counts
- missing setup requirements
- readiness/lifecycle decisions
- available context actions
```

The frontend must not infer setup readiness beyond rendering backend-provided
`status` and `setup_status` values.

## 4. Guardrail

The contract is enforced by:

```text
frontend/src/app/shell/ReadinessPanel.test.tsx
frontend/tests/readinessPanelPatternContract.test.ts
```

The static contract blocks raw readiness markup outside the shared shell
component.

## 5. Next Extensions

Later slices can extend this pattern with:

```text
- backend-provided missing requirement list
- context action links
- read-only environment messaging
- blocked setup variants
- compact shell display
```

Those extensions should continue using backend-owned setup/context contracts.
