# GUI Frontend Architecture Cleanup

**Status:** delivered  
**Branch:** `codex/gui-frontend-architecture-cleanup`  
**Scope:** frontend ownership extraction without behavior or visual redesign.

## Goal

Extract the first GUI implementation into clear frontend ownership folders while
preserving backend contracts, tests, and the current operational visual
language.

## Delivered Structure

```text
frontend/src/app/
  App.tsx
  routes/
  shell/

frontend/src/modules/
  assets/
  catalog/
  evidence/
  integration-mapping/
  load-plan/
  master-data/
  order-release-generator/
  rates/
  moduleStatus.ts
  index.ts

frontend/src/platform/hooks/
  assets.ts
  catalog.ts
  evidence.ts
  integrationMapping.ts
  loadPlan.ts
  masterData.ts
  orderReleaseGenerator.ts
  platform.ts
  rates.ts

frontend/src/platform/types/
  assets.ts
  catalog.ts
  cockpit.ts
  evidence.ts
  integrationMapping.ts
  loadPlan.ts
  masterData.ts
  orderReleaseGenerator.ts
  platform.ts
  rates.ts
  shared.ts
```

`frontend/src/platform/hooks.ts` remains as the public compatibility barrel, so
existing imports can continue to use:

```text
../platform/hooks
../../platform/hooks
```

`frontend/src/platform/types.ts` follows the same barrel pattern for public type
imports:

```text
../platform/types
../../platform/types
```

## Ownership Model

```text
app/
  Shell composition, auth gate, routing orchestration, fallback states.

app/shell/
  Sidebar, page header, context summary, context switcher, preference controls.

app/routes/
  Backend navigation matching and module description metadata.

modules/
  Backend-backed module views and module-specific display helpers.

platform/
  API client, backend hooks, typed API contracts, auth/session, preferences,
  future desktop adapters.

ui/
  Reusable components, visual primitives, operational panels, status rendering.
```

## Guardrails Preserved

```text
- No business rules moved to the frontend.
- No validation or lifecycle logic duplicated in module views.
- No redesign during extraction.
- No real client data added to tests or docs.
- No direct desktop APIs in module views.
- No module-specific visual framework.
- OTM_RESOURCES remains untracked and untouched.
```

## Backend Ownership

The GUI still reads these concerns from backend contracts:

```text
- navigation
- session/auth state
- active project/profile/environment/domain context
- preferences
- module summaries
- object details
- actions
- jobs
- artifacts
- evidence
- validation/lifecycle status
```

## Validation

Executed after extraction:

```text
npm run lint
npm run test
npm run build
```

All passed locally.

Repeated after splitting `platform/types.ts` by domain:

```text
npm run lint
npm run test
npm run build
```

## Next Refactor Candidates

The next cleanup slices should stay incremental:

```text
1. Split platform/types.ts by domain while preserving a public barrel.
2. Add module README files only when module-local widgets start to grow.
3. Introduce token files for theme/status/density after the current CSS is audited.
4. Add an internal component gallery or Storybook using `GUI_COMPONENT_GALLERY_PLAN.md` after shared UI patterns stabilize.
```

Do not start a broad visual redesign as part of these cleanup slices.
