# GUI Selected Object Pattern Contract

**Status:** delivered  
**Branch:** `codex/gui-selected-object-contract`  
**Scope:** shared frontend rendering for selected object detail panels.

## 1. Decision

Module detail side panels must use the shared `SelectedObjectPanel` component
instead of recreating aside, selected state, field grid, action area, or detail
stack markup inside module views.

This keeps selected object identity, status, metadata, backend actions, loading
state, and empty state consistent across modules.

## 2. Current Contract

Use:

```text
SelectedObjectPanel
```

For:

```text
- selected batch detail
- selected package detail
- selected asset detail
- selected evidence detail
- selected template detail
- selected mapping definition detail
- selected catalog macro object detail
```

Each usage must provide:

```text
- ariaLabel
- emptyText
- status
```

Optional data should use the shared props:

```text
- title
- subtitle
- fields
- actions
- isLoading
- loadingText
- children for domain-specific detail rows
```

Do not use raw `module-template-side`, `detail-stack`, `detail-grid`, or
`detail-actions` markup inside module views.

## 3. Boundary

The component owns layout and selected object affordances only.

Backend remains responsible for:

```text
- selected object identity and metadata
- lifecycle status
- available actions
- permission and disabled reasons
- artifacts and evidence references
- validation decisions
```

The frontend must not infer lifecycle or permission rules from selected object
fields.

## 4. Guardrail

The contract is enforced by:

```text
frontend/tests/selectedObjectPatternContract.test.ts
frontend/src/ui/components.test.tsx
```

The static contract blocks raw selected panel layout classes in module views and
requires an accessible label for each `SelectedObjectPanel` usage.

## 5. Next Extensions

Later slices can extend this pattern with:

```text
- tabs for detail sections
- expandable field groups
- evidence/artifact side links
- permission explanations
- read-only and blocked variants
```

Those extensions should continue using backend-owned object and action data.
