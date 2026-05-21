# GUI Component Gallery Plan

**Status:** delivered for MVP coverage
**Branch:** `codex/gui-component-gallery-coverage`
**Scope:** component gallery or Storybook-equivalent plan for shared GUI patterns.

## 1. Purpose

OTM Workbench needs a visible component workbench for shared shell, UI kit,
module workspace, state, action, artifact, blocker, and feedback patterns.

This plan defines the gallery scope before adding tooling. The first version can
be an internal route or static component gallery; Storybook can be added later
when frontend tooling work is worth the extra dependency and maintenance cost.

## 2. Principles

```text
- Backend-first: stories use synthetic contract-shaped data, not frontend-owned
  business rules.
- Client-safe: no real client names, payload values, identifiers, CNPJ, CPF, or
  customer-specific screenshots.
- Contract-aligned: every displayed pattern points back to a GUI contract.
- Token-driven: light, dark, system, density, and sidebar behaviors use the same
  tokens as the application.
- Desktop-ready: examples should fit browser first and avoid assumptions that
  block a future desktop wrapper.
```

## 3. Gallery Options

### Option A - Internal Component Gallery Route

Use an authenticated development/admin-only route served by the existing Vite
app.

Current implementation route:

```text
/__gui/component-gallery
```

The route is rendered by `frontend/src/app/routes/ComponentGalleryRoute.tsx`
and is intentionally not sourced from backend navigation. It remains an
internal synthetic workbench for shared pattern review.

The authenticated app flow is covered by
`frontend/src/app/AppComponentGalleryRoute.test.tsx`, which verifies that
`/__gui/component-gallery` renders after login while the sidebar keeps only
backend-provided navigation items.

Best for:

```text
- lowest initial tooling cost
- validating components inside the real app shell
- using existing React Query/test setup
- avoiding Storybook setup while GUI contracts are still moving
```

Constraints:

```text
- must stay hidden from normal backend navigation unless explicitly enabled
- must use synthetic fixtures only
- must not become a second implementation surface for product behavior
```

### Option B - Storybook

Add Storybook after component APIs stabilize.

Best for:

```text
- visual review of component variants
- eventual design handoff and Figma alignment
- isolated interaction states
- screenshot/a11y automation later
```

Constraints:

```text
- requires new frontend tooling dependencies
- needs fixture discipline to avoid fake product logic
- should not replace app-level integration tests
```

## 4. Initial Pattern Coverage

| Pattern | Required Examples | Data | MVP Route Coverage |
|---|---|---|---|
| WorkbenchShell | authenticated, compact, collapsed-sidebar reference | synthetic navigation and preferences | delivered through shell reference panel |
| LoginPanel | empty state | synthetic auth context | delivered as isolated shell example |
| PageHeader | title, subtitle, metadata, primary action | synthetic backend actions | delivered |
| ContextSummary | ready context | synthetic active context | delivered |
| ContextSwitcher | ready selectors preview | synthetic projects/profiles/environments | delivered as disabled visual preview |
| ReadinessPanel | ready setup status | synthetic setup status | delivered |
| PreferenceControls | light/default and compact/dark | synthetic user preferences | delivered |
| MetricGrid | normal counts, warning, zero/empty | synthetic metrics | delivered |
| ModuleWorkspaceLayout | object/detail workspace | synthetic object list | delivered |
| ModuleObjectList | selected, long labels | synthetic objects | delivered |
| SelectedObjectPanel | selected object and actions | synthetic selected object | delivered |
| DetailList | rows and long metadata | synthetic detail rows | delivered |
| OperationalPanel | active panels for fixtures, auth, context, preferences, actions | synthetic jobs/artifacts/evidence/context | delivered |
| ArtifactList | downloadable artifact, status-only artifact, evidence row | synthetic artifact/evidence rows | delivered |
| BlockerPanel | blocked state | synthetic blockers | delivered |
| ActionBar | enabled, disabled with reason, running action | synthetic backend actions | delivered |
| FeedbackMessage | success and error | synthetic text | delivered |
| StatePanel | loading and unavailable | synthetic state text | delivered |
| StatusChip | ready, blocked, error, read-only, pending, active | synthetic statuses | delivered |
| Button/IconButton | primary, secondary, disabled, icon-only | synthetic commands | delivered |

The gallery route intentionally shows `ContextSwitcher` as a disabled synthetic
preview rather than mounting the production component. The production
`ContextSwitcher` owns backend-backed project, profile, and environment hooks,
so the gallery keeps the selector shape visible without creating a second data
loading surface or hidden mock backend.

## 5. Fixture Rules

Initial fixture source:

```text
frontend/src/test/fixtures/gui.ts
```

Current shared UI kit and gallery consumers:

```text
frontend/src/ui/components.test.tsx
frontend/src/app/routes/ComponentGalleryRoute.tsx
frontend/src/app/AppComponentGalleryRoute.test.tsx
frontend/src/app/routes/ComponentGalleryRoute.test.tsx
frontend/tests/componentGalleryRouteContract.test.ts
```

Fixtures must:

```text
- live under a clearly synthetic frontend fixture location when implemented
- use `.example.test`, `.synthetic`, or equivalent fake identifiers
- mirror backend response shapes where possible
- include long labels and missing optional fields
- include disabled/read-only/blocked states
- avoid any real client/customer data
```

Fixtures must not:

```text
- call real backend endpoints
- contain production secrets
- encode business decisions not present in backend contracts
- replace API contract tests
```

## 6. Rollout

```text
1. Create synthetic fixture builders for shared platform objects. Done.
2. Add internal gallery route or Storybook shell with no production navigation.
   Done.
3. Add primitive UI kit examples. Done.
4. Add shell examples. Done.
5. Add module workspace/object display examples. Done.
6. Add operational/artifact/evidence examples. Done.
7. Add visual/a11y screenshot checks when browser automation is reliable.
8. Require new reusable components to add a gallery example or explicit
   exception.
```

## 7. Verification

Before accepting the gallery implementation:

```text
npm run lint
npm run test
npm run build
git diff --check
```

When browser automation is available, verify:

```text
- desktop light mode
- desktop dark mode
- compact density
- collapsed sidebar
- mobile width below 900px
- long text and empty states
```

If browser automation is blocked by the Windows sandbox, record the blocked
attempt in the relevant GUI QA note.

Current gallery-specific browser QA status:

```text
GUI_GALLERY_VISUAL_QA_ATTEMPT.md
```
