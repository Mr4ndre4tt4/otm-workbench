# GUI Activity Row Pattern Contract

**Status:** delivered  
**Branch:** `codex/gui-activity-row-contract`  
**Scope:** shared frontend rendering for operational activity rows.

## 1. Decision

Operational activity rows must use the shared `ActivityRow` component instead
of recreating `activity-row` markup in cockpit or module screens.

This keeps recent job, recent evidence, and future activity rows consistent
inside `OperationalPanel`.

## 2. Current Contract

Use:

```text
ActivityRow
```

For:

```text
- recent jobs
- recent evidence
- operational activity summaries
- compact activity rows inside OperationalPanel
```

Do not use raw `activity-row` markup outside:

```text
frontend/src/ui/components/activity.tsx
```

## 3. Boundary

The component owns row presentation only.

Backend remains responsible for:

```text
- activity identity
- source module
- job/evidence status
- ordering
- visibility
- links/actions when future contracts support them
```

The frontend must not infer activity meaning or workflow state beyond rendering
backend-provided title, subtitle, and status.

## 4. Guardrail

The contract is enforced by:

```text
frontend/tests/activityRowPatternContract.test.ts
frontend/src/ui/components.test.tsx
```

The static contract blocks raw `activity-row` usage outside the shared UI
component implementation.

## 5. Next Extensions

Later slices can extend this pattern with:

```text
- backend-provided href/action
- timestamp metadata
- progress indicator
- severity icon
- compact/dense variants
```

Those extensions should continue consuming backend-owned activity metadata.
