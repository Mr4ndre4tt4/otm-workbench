# GUI Implementation Checklist

**Status:** delivered  
**Branch:** `codex/gui-implementation-checklist`  
**Scope:** required review checklist before adding or changing GUI screens, modules, visual patterns, or shell behavior.

## 1. Purpose

This checklist is the pre-flight and review gate for GUI work in OTM Workbench.

It keeps new UI work aligned with the backend-first architecture, shared UI kit,
shell contracts, decision log, exceptions register, and Linear project tracking.

## 2. Before Building

Confirm the work has:

```text
- Request classification: strategy, architecture, component, module screen,
  object pattern, dashboard, exception, or documentation update.
- Backend contract identified or explicitly marked missing.
- Data ownership confirmed: no durable product state lives only in frontend.
- Navigation, permissions, lifecycle, readiness, actions, jobs, artifacts,
  evidence, active context, and preferences remain backend-owned.
- Existing contracts checked in GUI_CONTRACT_INDEX.md.
- Existing reusable components checked before adding a new component.
- GUI_EXCEPTIONS_REGISTER.md reviewed for custom interaction needs.
- GUI_ACCESSIBILITY_QA_MATRIX.md reviewed for the required visual, keyboard,
  responsive, console, and client-data-safe QA baseline.
- GUI_DECISIONS_LOG.md reviewed for stack, shell, theme, desktop, and ownership
  decisions.
- GUI_FOUNDATION_CONSOLIDATION_REVIEW.md checked when the work depends on a
  stacked GUI branch sequence.
- Linear updated or planned for the delivery slice.
- Shared synthetic examples checked in `frontend/src/test/fixtures/gui.ts`
  before adding one-off fixtures.
```

## 3. Component And Layout Rules

Use established components before creating new markup:

```text
- PageHeader for page identity and backend actions.
- WorkbenchShell for app frame, sidebar, topbar, sign out, and preferences.
- LoginPanel for unauthenticated access.
- WorkbenchRoute for cockpit, module route dispatch, placeholders, and unknown
  route state.
- ModuleWorkspaceLayout for standard object/detail module workspaces.
- ModuleWorkspaceSide or SelectedObjectPanel for side panels.
- MetricGrid for dashboard counters.
- ModuleObjectList for selectable work queues or object lists.
- DetailList for detail rows and related records.
- OperationalPanel for jobs, artifacts, evidence, and operational sections.
- ArtifactList for compact artifact/evidence rows.
- BlockerPanel for blocker summaries.
- ActionBar for backend-provided actions.
- FeedbackMessage for inline success and error text.
- StatePanel for loading and unavailable states.
- StatusChip for backend statuses.
- Button and IconButton for commands.
```

Custom layouts or interactions require an approved entry in
`GUI_EXCEPTIONS_REGISTER.md` before implementation.

## 4. Required States

Every GUI slice must account for relevant states:

```text
- loading
- empty
- no results
- unavailable or API error
- warning
- success
- blocked
- disabled by permission
- read-only
- long labels
- missing optional fields
```

Do not invent frontend lifecycle states that conflict with backend readiness,
permission, or action contracts.

## 5. Accessibility And Responsiveness

Before review, confirm:

```text
- Buttons and icon buttons have accessible names.
- Interactive rows expose pressed/selected state when applicable.
- Lists, panels, forms, and workspaces have useful aria labels.
- Text does not overlap at supported desktop and mobile widths.
- Shared tokens handle light, dark, system, density, and sidebar preferences.
- New CSS belongs in the correct layer and does not bypass ownership contracts.
```

## 6. Documentation And Tracking

Before committing:

```text
- Update or add the relevant GUI_*_CONTRACT.md.
- Add the contract to GUI_CONTRACT_INDEX.md.
- Update GUI_ACCESSIBILITY_QA_MATRIX.md when the work changes required route,
  viewport, preference, keyboard, or browser evidence coverage.
- Update GUI_MVP1_PLAN.md if the work changes delivered scope.
- Update GUI_DECISIONS_LOG.md only when adding or superseding a decision.
- Update GUI_EXCEPTIONS_REGISTER.md for approved custom patterns.
- Update Linear with branch, delivered scope, validation, and notes.
```

## 7. Verification

Run the focused tests for the touched pattern plus the standard frontend gate:

```text
npm run lint
npm run test
npm run build
git diff --check
```

For visual or interaction changes, also run browser visual QA when the local
environment can launch a browser. If browser QA is blocked by the Windows
sandbox, document the attempted check instead of claiming it passed.

## 8. Client Data Rule

Do not use real client names, identifiers, documents, payload values, CNPJ, CPF,
or customer-specific secrets in GUI code, tests, docs, or screenshots.

Use synthetic examples only.
