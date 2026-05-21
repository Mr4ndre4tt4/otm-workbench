# GUI Status Chip Pattern Contract

**Status:** delivered  
**Branch:** `codex/gui-status-chip-contract`  
**Scope:** shared frontend rendering for status badges and lifecycle/status labels.

## 1. Decision

Status badges must use the shared `StatusChip` component instead of recreating
badge markup or `status-*` classes inside app, shell, or module views.

This keeps lifecycle, readiness, blocked, empty, success, and error treatments
visually consistent across navigation, lists, panels, metrics, artifacts, and
evidence references.

## 2. Current Contract

Use:

```text
StatusChip
```

For:

```text
- module status
- object status
- job/evidence/artifact status
- panel status
- metric status
- lifecycle/readiness labels
```

Do not use raw `status-chip` or `status-*` classes outside:

```text
frontend/src/ui/components/primitives.tsx
frontend/src/ui/components.css
```

## 3. Boundary

The component owns status label presentation only.

Backend remains responsible for:

```text
- status values
- lifecycle meaning
- readiness decisions
- permission and blocked reasons
- validation severity
- action availability
```

The frontend may normalize display casing, but it must not infer lifecycle or
permission meaning from arbitrary strings beyond applying shared visual tokens.

## 4. Guardrail

The contract is enforced by:

```text
frontend/tests/statusChipPatternContract.test.ts
frontend/src/ui/components.test.tsx
```

The static contract blocks raw `status-chip` and `status-*` class usage outside
the shared UI component implementation.

## 5. Next Extensions

Later slices can extend this pattern with:

```text
- explicit semantic status groups
- accessible status descriptions
- backend-provided severity mapping
- icon variants for warning/error/success
- tooltip explanations for blocked/disabled states
```

Those extensions should continue using backend-owned status semantics.
