# GUI Shared Metrics

**Status:** implemented
**Branch:** `codex/gui-shared-metrics`

## Objective

Add a reusable metric grid foundation so module overview screens do not
recreate card layout, labels, values, and status chip placement independently.

This keeps the GUI consistent while preserving backend ownership of metric
meaning, values, and severity/status interpretation.

## Component

`MetricGrid` is exported by the public `frontend/src/ui/components.tsx` barrel
and implemented in `frontend/src/ui/components/metrics.tsx`.

It receives caller-provided metric items:

```text
- key;
- label;
- value;
- optional status.
```

The component only renders layout. It does not calculate module health,
permissions, lifecycle gates, or OTM readiness.

## First Consumers

```text
- Project Cockpit activity metrics;
- Rates Studio summary metrics.
```

## Guardrails

```text
- No backend contract changes.
- No client-specific examples.
- No frontend lifecycle decision logic.
- Rates severities remain sourced from the Rates summary contract.
- Cockpit counters remain sourced from the Project Cockpit summary contract.
```

## Validation

Commands executed:

```text
cd frontend
npm run lint
npm run test
npm run build
```
