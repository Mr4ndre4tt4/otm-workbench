# GUI Module Action Surfaces Contract

**Status:** delivered  
**Branch:** `codex/gui-module-action-surfaces`  
**Linear:** `OTM-70`  
**Scope:** module action placement, disabled reasons, execution feedback, and backend-owned action metadata.

## 1. Purpose

Backend-backed module screens should expose actions through predictable shared
surfaces instead of scattering module-local buttons across each view.

This contract defines where actions belong, which component owns rendering, and
which decisions must stay in backend contracts.

## 2. Source Components

Use the existing shared patterns:

```text
ActionBar
Button
FeedbackMessage
PageHeader
SelectedObjectPanel
OperationalPanel
ArtifactList
StatePanel
```

Action rendering must flow through `ActionBar` when the backend returns
`available_actions`. Local buttons are allowed only for simple UI commands or
artifact download affordances that already come from guarded backend URLs.

## 3. Backend Ownership

The frontend must not infer whether an action is available, safe, primary,
disabled, or permitted from object status, lifecycle labels, row counts, module
name, or local heuristics.

Backend remains authoritative for:

```text
- action key
- action label
- method
- href
- variant
- icon_key
- disabled flag
- disabled reason
- permission
- requires_confirmation
- result_hint
- action ordering
- lifecycle and readiness gates
```

Frontend may own:

```text
- placement in the approved surface slot
- click dispatch
- running spinner/text
- inline success feedback
- inline error feedback from backend error envelope
- query invalidation triggered by backend result_hint
```

## 4. Action Surface Slots

Module screens may use these action slots:

```text
1. Page header actions
   Context-wide module commands returned by the module summary contract.

2. Selected object actions
   Object-specific commands returned by the selected detail contract.

3. Operational row actions
   Download/open/retry controls on artifact, evidence, job, or generated-file
   rows, only when the backend exposes guarded href/action metadata.

4. Future bulk actions
   Multi-select commands after backend contracts expose selection scope,
   capability, disabled reasons, and confirmation requirements.
```

Do not create a new action surface for one module unless the exception is
recorded in `GUI_EXCEPTIONS_REGISTER.md`.

## 5. Feedback Rules

Action feedback must use shared `FeedbackMessage` and backend error messages
when available.

Required behavior:

```text
- running: disable the active action and show shared running text
- success: show a concise action completion message
- backend error: show the backend error envelope message
- unknown error: show a generic safe failure message
- disabled by permission: render disabled state and backend disabled_reason
- read-only: render disabled actions from backend metadata
- unsupported method: do not execute locally; leave capability to backend contract
- requires confirmation: do not execute until a confirmation pattern exists
```

Current MVP1 implementation supports direct `POST` execution in Rates Studio.
Confirmation dialogs, grouped actions, and richer method handling remain future
extensions and must stay backend-metadata driven.

## 6. Module Matrix

| Module | Current action surface | Next allowed extension |
|---|---|---|
| Rates Studio | Page header actions, selected batch actions, artifact download action, FeedbackMessage | Confirmation handling and result_hint expansion |
| Catalog Core | No executable actions surfaced | Catalog validation actions when backend exposes available_actions |
| Load Plan | No executable actions surfaced | Build/export/checklist actions when backend exposes available_actions |
| Assets Library | No executable actions surfaced | Asset upload/download/version actions through guarded contracts |
| Evidence Hub | No executable actions surfaced | Evidence export/open actions through guarded contracts |
| Master Data | No executable actions surfaced | Template build/package actions when backend exposes available_actions |
| Order Release Generator | No executable actions surfaced | XML preview/generate/import actions when backend exposes available_actions |
| Integration Mapping Studio | No executable actions surfaced | Preview/test mapping actions when backend exposes available_actions |

## 7. Client-Safe Rules

Action examples and tests must use synthetic content only.

Do not introduce:

```text
- real client names
- real endpoint payload bodies
- real document identifiers
- secrets
- local artifact file paths
- raw XML/JSON payload bodies
```

Action labels in examples should be generic, such as `Validate`, `Build`,
`Export`, `Preview`, `Download`, `Approve`, or `Run`.

## 8. Implementation Rule

When adding actions to a module:

```text
1. Confirm the backend response exposes available_actions or guarded row action metadata.
2. Render backend action lists through ActionBar.
3. Keep action execution in a module adapter/hook, not inside shared UI components.
4. Respect backend disabled and disabled_reason exactly.
5. Do not execute disabled actions.
6. Do not execute unsupported methods locally.
7. Show FeedbackMessage for success/error outcomes.
8. Invalidate only the queries implied by backend result_hint or explicit module contract.
9. Add component/module tests for dispatch, disabled state, feedback, and invalidation.
10. Update this matrix when a module gains a new action surface.
```

## 9. Guardrails

This contract is enforced by:

```text
frontend/tests/guiModuleActionSurfacesContract.test.ts
frontend/tests/actionPatternContract.test.ts
frontend/src/app/shell/ActionBar.test.tsx
frontend/tests/feedbackMessagePatternContract.test.ts
```

The guardrails keep the contract discoverable, block direct
`available_actions.map` rendering in module views, and keep disabled reasons and
feedback centralized through shared patterns.

## 10. Acceptance Criteria

This contract is accepted when:

```text
- the contract is linked from GUI_CONTRACT_INDEX.md
- the contract is linked from GUI_MVP1_PLAN.md
- action surface slots are documented
- backend-owned action metadata is explicit
- feedback states are documented
- current module matrix is documented
- client-safe rules are explicit
- static tests cover discoverability and core wording
```
