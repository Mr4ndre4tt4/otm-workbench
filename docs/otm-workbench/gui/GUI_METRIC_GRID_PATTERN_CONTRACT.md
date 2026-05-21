# GUI Metric Grid Pattern Contract

**Status:** delivered  
**Branch:** `codex/gui-metric-grid-contract`  
**Scope:** shared frontend rendering for module summary metrics.

## 1. Decision

Module summary indicators must use the shared `MetricGrid` component instead
of recreating metric cards or metric row markup inside module views.

This keeps summary density, status chip placement, responsive behavior, and
accessibility consistent across the cockpit and module landing screens.

## 2. Current Contract

Use:

```text
MetricGrid
```

For:

```text
- module landing summary counts
- cockpit activity counters
- selected context/module health indicators
- implementation object summary metrics
```

Each usage must provide:

```text
- ariaLabel
- items
```

Do not use raw `metrics-grid` or `metric` card markup inside module views.

## 3. Boundary

The component owns metric rendering only.

Backend remains responsible for:

```text
- metric values
- metric severity/status meaning
- lifecycle readiness
- validation counts
- job/artifact/evidence counts
- permission and visibility decisions
```

The frontend must not infer readiness, approval, validation, or lifecycle
meaning from raw numeric values beyond displaying backend-provided status.

## 4. Guardrail

The contract is enforced by:

```text
frontend/tests/metricGridPatternContract.test.ts
frontend/src/ui/components.test.tsx
```

The static contract blocks raw metric grid classes in module views and requires
an accessible label for each module `MetricGrid` usage.

## 5. Next Extensions

Later slices can extend this pattern with:

```text
- trend indicators
- backend-provided tooltip/help text
- warning thresholds supplied by backend
- compact metric density variants
- click-through metric actions from backend
```

Those extensions should continue using backend-owned metric semantics.
