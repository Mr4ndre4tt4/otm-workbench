# GUI Module Object List

**Status:** implemented
**Branch:** `codex/gui-module-object-list`

## Objective

Add a reusable selectable object list for module overview screens.

This reduces repeated list-row markup while keeping module data, selection,
status, metadata, and actions owned by backend contracts and module adapters.

## Component

`ModuleObjectList` is exported by the public `frontend/src/ui/components.tsx`
barrel and implemented in `frontend/src/ui/components/lists.tsx`.

It receives:

```text
- object id;
- title;
- optional subtitle;
- metadata values;
- status;
- selected id;
- select callback.
```

The component renders selectable rows with stable accessibility semantics and
an empty state.

## First Consumer

Rates Studio now uses `ModuleObjectList` for recent rate batches.

The Rates screen still adapts backend batch summaries into display metadata:

```text
- table count;
- row count;
- issue count;
- backend status.
```

## Guardrails

```text
- No backend contract changes.
- No frontend lifecycle calculation.
- No frontend permission decisions.
- No client-specific sample data.
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
