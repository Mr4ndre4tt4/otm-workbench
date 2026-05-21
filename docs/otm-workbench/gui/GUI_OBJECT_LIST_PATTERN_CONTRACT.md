# GUI Object List Pattern Contract

**Status:** delivered  
**Branch:** `codex/gui-object-list-contract`  
**Scope:** shared frontend rendering for module primary object lists.

## 1. Decision

Module primary lists must use the shared `ModuleObjectList` component instead
of recreating list rows, selected states, or clickable object markup in each
module.

This keeps list density, selection behavior, status chip placement, empty
state, and accessibility treatment consistent across Rates, Catalog, Load Plan,
Assets, Evidence, Master Data, Order Release Generator, and Integration Mapping.

## 2. Current Contract

Use:

```text
ModuleObjectList
```

For:

```text
- module landing list
- selectable object queue
- primary object collection in list/detail module layouts
```

Each usage must provide:

```text
- ariaLabel
- emptyText
- items
- onSelect
- selectedId
```

Do not use raw `module-list` or `module-row` markup inside module views.

## 3. Boundary

The component owns list rendering and selection affordance only.

Backend remains responsible for:

```text
- list content
- status values
- available object actions
- lifecycle and permission decisions
- server-side filtering, sorting, and pagination when those contracts arrive
```

The frontend must not infer hidden lifecycle or permission rules from list row
metadata.

## 4. Guardrail

The contract is enforced by:

```text
frontend/tests/objectListPatternContract.test.ts
frontend/src/ui/components.test.tsx
```

The static contract blocks raw module list markup in module views and requires
an accessible label for each `ModuleObjectList` usage.

## 5. Next Extensions

Later slices can extend this pattern with:

```text
- search and filter controls
- sort controls
- bulk action selection
- pagination
- row action menu
- no-results state distinct from empty state
```

Those extensions should continue using backend-owned data and action contracts.
