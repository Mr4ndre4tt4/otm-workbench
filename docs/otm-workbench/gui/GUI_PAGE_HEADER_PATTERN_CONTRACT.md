# GUI Page Header Pattern Contract

**Status:** delivered  
**Branch:** `codex/gui-page-header-contract`  
**Scope:** shared frontend rendering for module and route page headers.

## 1. Decision

Module and route page headers must use the shared `PageHeader` component instead
of recreating page title, label, description, or header action markup inside
module views.

This keeps the first viewport signal consistent across modules and preserves
the backend-owned action pattern through `ActionBar`.

## 2. Current Contract

Use:

```text
PageHeader
```

For:

```text
- module landing headers
- cockpit header
- placeholder module headers
- unknown route headers
```

Each usage must provide:

```text
- label
- title
- description
```

Optional backend actions should flow through:

```text
- actions
```

Do not use raw `page-header` markup or module-level `<h1>` elements inside
module views.

## 3. Boundary

The component owns page header layout and the handoff to shared action
rendering only.

Backend remains responsible for:

```text
- route availability
- module visibility
- available actions
- action status/disabled reason
- lifecycle and permission decisions
```

The frontend must not infer route availability or module readiness from page
header text.

## 4. Guardrail

The contract is enforced by:

```text
frontend/tests/pageHeaderPatternContract.test.ts
```

The static contract blocks raw page header markup in app/module screens and
blocks module-level `<h1>` rendering outside `PageHeader`.

## 5. Next Extensions

Later slices can extend this pattern with:

```text
- backend-provided breadcrumbs
- context badges
- page-level read-only/blocked messaging
- compact header variants
- module help links
```

Those extensions should continue using backend-owned navigation and action
contracts.
