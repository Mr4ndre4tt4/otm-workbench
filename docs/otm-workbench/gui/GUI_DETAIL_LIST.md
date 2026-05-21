# GUI Detail List

**Status:** implemented
**Branch:** `codex/gui-detail-list`

## Objective

Add a reusable detail list for compact rows inside selected-object panels.

This creates a shared rendering pattern for module detail rows such as rate
batch tables, mapping rows, validation findings, asset versions, and load plan
steps while keeping module-specific data owned by backend contracts.

## Component

`DetailList` is exported by the public `frontend/src/ui/components.tsx` barrel
and implemented in `frontend/src/ui/components/lists.tsx`.

It receives:

```text
- aria label;
- row id;
- row title;
- metadata values;
- optional status;
- empty-state text.
```

The component does not calculate statuses, validations, permissions, or
lifecycle readiness.

## First Consumer

Rates Studio now uses `DetailList` for selected batch tables.

The Rates screen still adapts backend table summaries into:

```text
- table name;
- row count;
- backend table status.
```

## Guardrails

```text
- No backend contract changes.
- No frontend lifecycle calculation.
- No client-specific sample data.
- No hidden table payload rendering.
```

## Validation

Commands executed:

```text
cd frontend
npm run test -- components.test.tsx
npm run lint
npm run test
npm run build
```
