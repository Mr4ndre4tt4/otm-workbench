# GUI Operational Panel Pattern Contract

**Status:** delivered  
**Branch:** `codex/gui-operational-panel-contract`  
**Scope:** shared frontend rendering for operational panels and secondary work queues.

## 1. Decision

Operational collections must use the shared `OperationalPanel` component instead
of recreating panel cards in app or module screens.

This keeps secondary panels consistent for recent jobs, evidence, artifacts,
activity, and future operational queues.

## 2. Current Contract

Use:

```text
OperationalPanel
```

For:

```text
- recent jobs
- recent evidence
- artifact collections
- evidence collections
- secondary operational queues
```

Each usage must provide:

```text
- ariaLabel
- title
- status
- emptyText
- hasItems
```

Optional states should use:

```text
- isLoading
- loadingText
- className only for sanctioned layout variants
```

Do not use raw `className="panel"` card markup inside app or module screens.

## 3. Boundary

The component owns panel layout, header, status chip placement, loading state,
and empty state only.

Backend remains responsible for:

```text
- job status and progress
- artifact/evidence metadata
- item availability
- lifecycle and permission decisions
- activity ordering
- action availability
```

The frontend must not infer lifecycle, approval, or readiness decisions from
panel content.

## 4. Guardrail

The contract is enforced by:

```text
frontend/tests/operationalPanelPatternContract.test.ts
frontend/src/ui/components.test.tsx
```

The static contract blocks raw panel card markup in app/module screens and
requires an accessible label for each `OperationalPanel` usage.

## 5. Next Extensions

Later slices can extend this pattern with:

```text
- row primitives for activity rows
- panel-level action menus
- backend-provided no-results states
- polling/progress affordances
- warning/read-only/blocked variants
```

Those extensions should continue consuming backend-owned operational metadata.
