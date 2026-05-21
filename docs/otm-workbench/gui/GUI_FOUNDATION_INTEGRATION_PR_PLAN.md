# GUI Foundation Integration PR Plan

**Status:** delivered  
**Branch:** `codex/gui-foundation-integration-pr-plan`  
**Linear:** `OTM-72`  
**Scope:** integration pull request plan for the delivered GUI foundation stack.

## 1. Purpose

The GUI foundation now spans a long stack of small branches. This plan defines
how to review and integrate that stack without adding new module behavior during
the consolidation step.

The integration PR should be a reviewer-friendly packaging of delivered GUI
foundation work, not a feature expansion.

## 2. Integration Scope

Include delivered work covering:

```text
- GUI governance and backend ownership contracts
- React/Vite frontend shell foundation
- auth/session and active context rendering
- backend-owned navigation and preferences
- shared UI kit components
- CSS theme, density, sidebar, layout, and responsive layers
- backend-backed module list/detail screens
- Rates action/artifact/evidence GUI affordances
- synthetic fixtures and internal component gallery
- component ownership split
- module consistency, operational surface, action surface, and long-label guardrails
- design-system handoff and icon-family governance
```

Do not include:

```text
- new backend module behavior
- new real OTM execution flows
- new customer/client data examples
- new Figma file creation
- visual redesign beyond already-delivered CSS foundations
- browser pixel claims not backed by successful visual QA
```

## 3. Review Sections

Use these PR sections:

```text
1. Governance and backend ownership
2. Shell, routing, auth, context, preferences, and navigation
3. UI kit components and CSS layers
4. Backend-backed module screens
5. Rates Studio action/artifact/evidence affordances
6. Synthetic fixtures and component gallery
7. Module consistency, operational, action, and long-label guardrails
8. Design system/Figma handoff
9. Visual QA limitation and browser runtime fallback
```

Each section should call out the relevant docs, tests, and branch/issue range.

## 4. Branch And Issue Coverage

The integration PR should account for:

```text
OTM-55 GUI MVP1 planning foundation
OTM-56 GUI architecture strategy spec
OTM-57 GUI Foundation Stack - review published branches
OTM-58 Rates Studio GUI MVP - finish module workflow
OTM-60 GUI visual QA and accessibility pass
OTM-63 GUI foundation consolidation - review and merge stacked branches
OTM-64 GUI component gallery MVP - complete coverage matrix
OTM-65 GUI visual QA pass - gallery plus shell states
OTM-66 GUI frontend architecture cleanup - folder ownership and component split
OTM-67 GUI module screen consistency audit - backend-backed modules
OTM-68 GUI design system handoff - Figma and icon family evaluation
OTM-69 GUI module operational surfaces - artifacts evidence jobs blockers
OTM-70 GUI module action surfaces - backend actions disabled reasons feedback
OTM-71 GUI module long-label responsive regression coverage
OTM-72 GUI foundation integration PR plan
```

If any listed issue is already done, the PR should summarize it as delivered
evidence instead of reopening its scope.

## 5. Required Validation

Before opening or marking the integration PR ready:

```text
npm run lint
npm run test
npm run build
git diff --check
```

Also run a sensitive content scan over GUI docs, frontend source, and tests:

```text
rg -n "CNPJ|CPF|cliente real|NDD|BRF|ABR|[0-9]{2}\.[0-9]{3}\.[0-9]{3}/[0-9]{4}-[0-9]{2}|[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}" docs/otm-workbench/gui frontend/src/app frontend/src/modules frontend/src/ui frontend/src/test frontend/tests
```

Expected known findings are client-safety guardrails and the existing synthetic
`target_system: "NDD"` fixture only.

## 6. Browser QA Boundary

Browser visual QA remains limited until the browser runtime issue is resolved
or an approved external-browser fallback becomes part of the QA workflow.

The PR may cite:

```text
GUI_GALLERY_VISUAL_QA_ATTEMPT.md
GUI_BROWSER_RUNTIME_DIAGNOSTIC.md
GUI_SHELL_QA_CONTRACTS.md
```

The PR must not claim pixel-perfect visual evidence unless a successful browser
run, screenshot, or comparable visual QA artifact exists for that exact branch.

## 7. Linear And GitHub Handoff

Linear should contain:

```text
- integration issue link
- branch name
- validation evidence
- known browser QA limitation
- clear next step after integration
```

GitHub PR should contain:

```text
- review section checklist
- validation commands and results
- no-real-client-data statement
- OTM_RESOURCES/ excluded statement
- browser QA limitation
- follow-up issues for visual/accessibility QA or Figma handoff
```

## 8. PR Draft Body

Suggested PR body:

```text
## Summary

Integrates the delivered GUI foundation stack for OTM Workbench MVP1. This PR
packages the shell, routing, shared UI kit, CSS layers, backend-backed module
screens, component gallery, GUI governance contracts, and module guardrails into
a single reviewable foundation.

## Review Sections

- Governance and backend ownership
- Shell/routing/auth/context/preferences/navigation
- UI kit components and CSS layers
- Backend-backed module screens
- Rates Studio action/artifact/evidence affordances
- Synthetic fixtures and component gallery
- Module consistency/action/operational/long-label guardrails
- Design system/Figma handoff
- Browser QA limitation

## Validation

- npm run lint
- npm run test
- npm run build
- git diff --check
- sensitive content scan

## Safety

- No real client data added.
- `OTM_RESOURCES/` remains untracked/uncommitted.
- Backend remains source of truth for navigation, permissions, lifecycle,
  actions, jobs, artifacts, evidence, active context, and user preferences.

## Known Limitation

Browser visual QA is documented but not fully proven in the current browser
runtime. No pixel-perfect visual claim is made by this PR.
```

## 9. Acceptance Criteria

This plan is accepted when:

```text
- it is linked from GUI_CONTRACT_INDEX.md
- it is referenced by GUI_FOUNDATION_CONSOLIDATION_REVIEW.md
- review sections and excluded scope are explicit
- validation commands and sensitive scan are documented
- browser QA limitation is explicit
- Linear/GitHub handoff expectations are documented
```
