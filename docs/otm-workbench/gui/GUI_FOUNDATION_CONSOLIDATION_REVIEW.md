# GUI Foundation Consolidation Review

**Status:** refreshed
**Branch:** `codex/gui-foundation-consolidation-refresh`
**Linear:** `OTM-63`
**Scope:** review and consolidation path for the current GUI foundation branch stack through OTM-71.

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

## 3. Current Branch Stack

The current GUI foundation stack now includes the original foundation branches
plus the follow-up contracts and guardrails completed after this review first
landed.

Core foundation branches:

```text
codex/gui-synthetic-fixtures-foundation
codex/gui-fixtures-ui-kit-tests
codex/gui-internal-component-gallery-shell
codex/gui-gallery-app-route-guardrail
codex/gui-foundation-consolidation-review
```

Follow-up GUI branches now stacked above the original review:

```text
codex/gui-component-gallery-coverage
codex/gui-visual-qa-gallery-shell-states
codex/gui-frontend-ownership-component-split
codex/gui-module-screen-consistency-audit
codex/browser-runtime-diagnostic
codex/gui-design-system-handoff
codex/gui-module-operational-surfaces
codex/gui-module-action-surfaces
codex/gui-long-label-responsive-coverage
codex/gui-foundation-consolidation-refresh
```

These can still be reviewed as separate PRs, but the recommended path is now a
single integration review that preserves the logical sections below.

## 4. Review Order

Recommended review sequence:

```text
1. Synthetic fixtures and client-data guardrails.
2. UI kit tests consuming shared fixtures.
3. Internal component gallery route.
4. App-level route guardrail proving the gallery is authenticated and outside
   backend-owned production navigation.
5. Component gallery coverage matrix and gallery route checks.
6. Browser visual QA attempts, runtime fallback documentation, and completed
   Playwright fallback evidence.
7. Component ownership split and frontend architecture cleanup.
8. Module screen consistency audit across backend-backed modules.
9. Design system/Figma handoff and icon-family governance.
10. Module operational surfaces contract.
11. Module action surfaces contract.
12. Long-label responsive guardrail.
13. This refreshed consolidation review.
14. OTM-77 shell/Project Cockpit browser visual QA evidence.
15. OTM-78 Rates Studio browser visual and keyboard QA evidence.
```

The merge/review path should not add new visual behavior. It should prove that
the current behavior is coherent and ready for the next GUI workstream.

## 5. Known Risks

```text
- The in-app Browser plugin remains unavailable in this Codex session, but
  Playwright CLI fallback evidence is now captured for shell/Project Cockpit
  and Rates Studio in OTM-77 and OTM-78.
- frontend/src/ui/components.tsx now acts as the public UI kit barrel after the
  planned ownership split into internal component families.
- GUI_FRONTEND_ARCHITECTURE.md now reflects accepted/current structure while
  later cleanup docs describe delivered slices.
- Module screens share patterns and have consistency, operational surface,
  action surface, and long-label guardrails. Richer module GUI work still needs
  additional module-specific visual QA and accessibility passes.
- The branch stack is long. Merge/PR review should avoid mixing this foundation
  consolidation with new module behavior.
```

These risks are tracked in Linear:

```text
OTM-64 GUI component gallery MVP - complete coverage matrix
OTM-65 GUI visual QA pass - gallery plus shell states
OTM-66 GUI frontend architecture cleanup - folder ownership and component split
OTM-67 GUI module screen consistency audit - backend-backed modules
OTM-68 GUI design system handoff - Figma and icon family evaluation
OTM-69 GUI module operational surfaces - artifacts evidence jobs blockers
OTM-70 GUI module action surfaces - backend actions disabled reasons feedback
OTM-71 GUI module long-label responsive regression coverage
OTM-77 Browser visual QA evidence - shell and Project Cockpit
OTM-78 Rates GUI visual and keyboard QA slice
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

Prepare a GUI foundation integration PR that groups the delivered stack into
review sections instead of treating the current branch chain as unrelated work.

Use `GUI_FOUNDATION_INTEGRATION_PR_PLAN.md` as the concrete PR checklist and
handoff artifact.

Recommended PR sections:

```text
1. Governance and backend ownership contracts.
2. Shell, routing, auth, context, preferences, and navigation.
3. UI kit components, CSS layers, and responsive guardrails.
4. Backend-backed module screens.
5. Component gallery and synthetic fixtures.
6. Module consistency/action/operational contracts.
7. Visual QA evidence and browser runtime fallback.
```

After this integration review, the next GUI work should be either:

```text
- a narrow module-specific visual/accessibility QA pass, starting with
  Integration Mapping Studio or the internal component gallery; or
- a first Figma/design-system handoff task using the accepted contracts.
```

Avoid adding new module behavior inside the consolidation PR.
