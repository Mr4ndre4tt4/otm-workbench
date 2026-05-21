# GUI Shared Operational Panels

**Status:** implemented
**Branch:** `codex/gui-shared-operational-lists`

## Objective

Start a reusable GUI panel foundation for operational lists used by Project
Cockpit, Rates Studio, Evidence Hub, jobs, artifacts, and future module detail
screens.

This slice keeps the backend as the source of truth. It does not add frontend
business rules, local artifact path handling, or module-specific lifecycle
decisions.

## Component

`OperationalPanel` is exported by the public
`frontend/src/ui/components.tsx` barrel and implemented in
`frontend/src/ui/components/panels.tsx`.

It centralizes:

```text
- panel shell;
- title and status chip;
- loading state;
- empty state;
- caller-provided row content.
```

The component intentionally does not know about Rates, jobs, evidence, or
artifact schemas. Module screens continue to shape rows from backend contracts.

## First Consumers

```text
- Project Cockpit recent jobs;
- Project Cockpit recent evidence;
- Rates Studio batch artifacts;
- Rates Studio batch evidence.
```

## Guardrails

```text
- No hardcoded module permissions.
- No frontend lifecycle decisions.
- No client-specific sample data.
- No local artifact file path rendering.
- No new backend contract in this slice.
```

## Validation

Commands executed:

```text
cd frontend
npm run lint
npm run test
```
