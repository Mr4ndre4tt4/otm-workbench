# GUI Synthetic Fixtures Contract

**Status:** delivered  
**Branch:** `codex/gui-synthetic-fixtures-foundation`  
**Scope:** shared synthetic frontend fixtures for component tests and future component gallery examples.

## 1. Purpose

`frontend/src/test/fixtures/gui.ts` is the first shared fixture source for GUI
component examples.

It gives the future component gallery and current component tests a single
place for synthetic backend-shaped examples instead of scattering one-off
fixtures through screens and tests.

## 2. Fixture Scope

The first fixture set covers:

```text
- backend navigation items
- user preferences for light/default and compact/dark states
- context/shell reference values for gallery-only previews
- backend available actions
- metric grid items
- module object list rows
- detail list rows
- artifact/evidence list rows
- blocker panel rows
```

## 3. Rules

Fixtures must:

```text
- use synthetic identifiers and labels only
- keep backend-shaped fields where possible
- include long labels for responsive checks
- include empty/blocked/read-only/status-only cases when useful
- stay reusable across component tests and gallery examples
```

Fixtures must not:

```text
- call backend endpoints
- include real client names, payload values, CNPJ, CPF, or secrets
- encode product business rules that are not already represented in backend
  contracts
- replace API contract tests or module integration tests
```

## 4. Current Files

```text
frontend/src/test/fixtures/gui.ts
frontend/src/test/fixtures/gui.test.ts
frontend/src/app/routes/ComponentGalleryRoute.tsx
frontend/src/app/routes/ComponentGalleryRoute.test.tsx
frontend/src/app/AppComponentGalleryRoute.test.tsx
frontend/src/ui/components.test.tsx
frontend/tests/componentGalleryRouteContract.test.ts
frontend/tests/guiSyntheticFixturesUsage.test.ts
```

## 5. Current Consumers

`frontend/src/ui/components.test.tsx` is the first shared UI kit consumer. It
uses the synthetic metrics, module objects, detail rows, artifact rows, and
blocker rows instead of local one-off examples.

`frontend/src/app/routes/ComponentGalleryRoute.tsx` is the first internal
runtime consumer. It renders the same synthetic contract-shaped examples under
`/__gui/component-gallery`, outside backend-owned production navigation.

The gallery also uses synthetic navigation and preference fixtures to show
shell, theme, density, and context preview states without calling backend hooks
from the internal route.

`frontend/src/app/AppComponentGalleryRoute.test.tsx` covers the authenticated
app route path and confirms the component gallery is not introduced as a
backend navigation item.

## 6. Gallery Link

`GUI_COMPONENT_GALLERY_PLAN.md` expects synthetic contract-shaped data. These
fixtures are the starting point for that gallery, whether the first
implementation is an internal route or Storybook.

## 7. Guardrails

```text
frontend/src/test/fixtures/gui.test.ts
frontend/tests/componentGalleryRouteContract.test.ts
frontend/tests/guiSyntheticFixturesContract.test.ts
frontend/tests/guiSyntheticFixturesUsage.test.ts
```

The tests verify the fixture shape and keep the fixture contract linked from
the gallery plan, implementation checklist, and shared UI kit tests.
