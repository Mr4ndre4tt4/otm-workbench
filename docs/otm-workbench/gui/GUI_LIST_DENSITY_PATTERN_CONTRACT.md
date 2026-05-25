# GUI List Density Pattern Contract

**Status:** first slice delivered  
**Linear:** `OTM-143`  
**Scope:** shared density behavior for operational lists under seeded QA or
project-volume data.

## Purpose

Operational lists must stay scannable when synthetic QA runs or real projects
create many objects.

This first slice improves first-viewport signal without changing backend
contracts:

```text
- consistent truncation for long object ids and labels
- native title text for full values
- optional visible-row cap
- selected-object pinning when the selected row is outside the initial cap
- visible "Showing X of Y" summary
```

## Ownership

The frontend only controls presentation density.

Backend remains source of truth for:

```text
- object ordering
- lifecycle status
- active/current context
- filters and presets such as recent, active, archived, and needs attention
- pagination and server-side search
```

When backend-owned list presets or pagination become available, modules should
prefer those contracts over client-only caps.

## Delivered First Slice

```text
Component: frontend/src/ui/components/lists.tsx
Style: frontend/src/ui/layouts.css
Tests: frontend/src/ui/components.test.tsx
Applied modules: Rates, Evidence Hub, Assets Library, and Admin jobs
```

Applied caps:

```text
- Rate batches: 12 visible rows
- Evidence entries: 12 visible rows
- Assets: 12 visible rows
- Admin jobs: 10 visible rows
```

## Acceptance

```text
- The selected object remains visible even when it is outside the first rows.
- Long labels truncate visually but preserve full text through title attributes.
- Lists show a clear visible-count summary when capped.
- Existing module functional flows keep passing.
- This pattern does not replace backend-owned filters, presets, or pagination.
```
