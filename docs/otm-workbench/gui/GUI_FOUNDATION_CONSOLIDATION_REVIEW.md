# GUI Foundation Consolidation Review

**Status:** in progress
**Branch:** `codex/gui-foundation-consolidation-review`
**Linear:** `OTM-63`
**Scope:** review and consolidation path for the current GUI foundation branch stack.

## 1. Purpose

This review keeps the GUI foundation understandable before more visual or module
work is added.

The current stack has delivered a real web GUI foundation, but it now needs a
single review path so docs, tests, branches, and Linear do not drift apart.

## 2. Current Delivered Foundation

The current foundation includes:

```text
- backend-owned auth session, navigation, preferences, active context, actions,
  jobs, artifacts, and evidence contracts
- WorkbenchShell app frame with sidebar, topbar, preferences, sign out, and
  route content
- centralized WorkbenchRoute composition for cockpit, modules, placeholders,
  unknown routes, and the internal GUI gallery
- shared UI kit patterns for buttons, status chips, state panels, metrics,
  module object lists, selected object panels, detail lists, operational panels,
  artifacts, blockers, feedback, and activity rows
- CSS token and layer ownership split for theme, base, shell, components,
  layouts, density, sidebar, and responsive overrides
- module screens for Rates, Catalog, Load Plan, Assets, Evidence, Master Data,
  Order Release Generator, and Integration Mapping
- synthetic GUI fixture source at frontend/src/test/fixtures/gui.ts
- internal component gallery route at /__gui/component-gallery
```

## 3. Recent Branch Stack

The most recent foundation branches are:

```text
codex/gui-synthetic-fixtures-foundation
codex/gui-fixtures-ui-kit-tests
codex/gui-internal-component-gallery-shell
codex/gui-gallery-app-route-guardrail
codex/gui-foundation-consolidation-review
```

These should be reviewed in that order if they remain separate PRs. If the
branch stack is compressed into a single integration PR, preserve the same
logical sections in the PR description.

## 4. Review Order

Recommended review sequence:

```text
1. Synthetic fixtures and client-data guardrails.
2. UI kit tests consuming shared fixtures.
3. Internal component gallery route.
4. App-level route guardrail proving the gallery is authenticated and outside
   backend-owned production navigation.
5. This consolidation review.
```

The merge/review path should not add new visual behavior. It should prove that
the current behavior is coherent and ready for the next GUI workstream.

## 5. Known Risks

```text
- Browser visual QA is not fully proven in this Windows environment.
- frontend/src/ui/components.tsx now acts as the public UI kit barrel after the
  planned ownership split into internal component families.
- GUI_FRONTEND_ARCHITECTURE.md now reflects accepted/current structure while
  later cleanup docs describe delivered slices.
- Module screens share patterns, but they still need a consistency audit before
  richer module-specific GUI work.
```

These risks are tracked in Linear:

```text
OTM-64 GUI component gallery MVP - complete coverage matrix
OTM-65 GUI visual QA pass - gallery plus shell states
OTM-66 GUI frontend architecture cleanup - folder ownership and component split
OTM-67 GUI module screen consistency audit - backend-backed modules
OTM-68 GUI design system handoff - Figma and icon family evaluation
```

## 6. Required Verification

Before accepting this consolidation slice:

```text
npm run lint
npm run test
npm run build
git diff --check
```

Also confirm:

```text
- OTM_RESOURCES/ remains untracked and uncommitted.
- no real client data, CNPJ, CPF, raw payloads, or secrets were introduced.
- Linear has the branch, scope, validation, and next-step issues updated.
```

## 7. Recommendation

Proceed with `OTM-63` first, then complete `OTM-64`, then run `OTM-65`.

Do not start a larger GUI module expansion or Figma/icon-family effort until
the foundation stack is reviewed and the component gallery covers the core
states needed for visual QA.
