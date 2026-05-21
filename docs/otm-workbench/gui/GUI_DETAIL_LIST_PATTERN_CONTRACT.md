# GUI Detail List Pattern Contract

**Status:** delivered  
**Branch:** `codex/gui-detail-list-contract`  
**Scope:** shared frontend rendering for selected object detail lists.

## 1. Decision

Module detail rows must use the shared `DetailList` component instead of
recreating internal table/list row markup inside module views.

This keeps secondary detail sections consistent for tables, load sequences,
assets, evidence references, template fields, schema documents, mappings, and
other selected object details.

## 2. Current Contract

Use:

```text
DetailList
```

For:

```text
- selected object table rows
- selected object child collections
- artifact/evidence/reference rows
- template fields and columns
- mapping/schema/load sequence rows
```

Each usage must provide:

```text
- ariaLabel
- emptyText
- items
```

Do not use raw `table-list` or `table-list-item` markup inside module views.

## 3. Boundary

The component owns row rendering and empty detail state only.

Backend remains responsible for:

```text
- child collection content
- row status values
- artifact and evidence metadata
- validation issue counts
- sequencing and dependency meaning
- permission and lifecycle decisions
```

The frontend must not infer OTM dependency, lifecycle, or validation rules from
row presentation data.

## 4. Guardrail

The contract is enforced by:

```text
frontend/tests/detailListPatternContract.test.ts
frontend/src/ui/components.test.tsx
```

The static contract blocks raw detail row layout classes in module views and
requires an accessible label for each `DetailList` usage.

## 5. Next Extensions

Later slices can extend this pattern with:

```text
- compact/dense row variants
- sortable row metadata
- row-level actions
- grouped detail sections
- no-results state distinct from empty state
```

Those extensions should continue using backend-owned data and action contracts.
