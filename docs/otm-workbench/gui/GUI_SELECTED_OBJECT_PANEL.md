# GUI Selected Object Panel

**Status:** implemented
**Branch:** `codex/gui-selected-object-panel`

## Objective

Add a reusable selected-object panel foundation for module detail views.

The panel standardizes identity, status, metadata fields, backend-owned
actions, loading state, empty state, and caller-provided detail content without
owning module lifecycle or permission decisions.

## Component

`SelectedObjectPanel` is exported by the public
`frontend/src/ui/components.tsx` barrel and implemented in
`frontend/src/ui/components/panels.tsx`.

It receives:

```text
- title and optional subtitle;
- status;
- metadata fields;
- caller-rendered actions;
- loading and empty state labels;
- caller-rendered detail content.
```

## First Consumer

Rates Studio now uses `SelectedObjectPanel` for the selected rate batch detail
area.

The backend still provides:

```text
- batch status;
- available actions;
- disabled action state;
- table list and status.
```

## Guardrails

```text
- No backend contract changes.
- No frontend-only action availability.
- No lifecycle calculation in the UI kit.
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
