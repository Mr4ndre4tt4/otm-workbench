# GUI Action Pattern Contract

**Status:** delivered  
**Branch:** `codex/gui-action-pattern-contract`  
**Scope:** shared frontend rendering for backend-provided available actions.

## 1. Decision

Module screens must render backend-provided actions through the shared
`ActionBar` pattern instead of mapping `available_actions` directly to buttons.

This keeps action priority, disabled state, disabled reason, and running state
visually consistent across modules.

## 2. Current Contract

Use:

```text
ActionBar
```

For:

```text
- page header available actions
- selected object available actions
- backend-provided action lists
```

Do not map `available_actions` directly in module views.

## 3. Boundary

The GUI action component owns rendering and dispatch only.

Backend remains responsible for:

```text
- action availability
- action ordering
- action method and href
- primary/secondary variant
- disabled flag
- disabled reason
- permission and capability decisions
- result hint
- confirmation requirements
```

The frontend must not infer permissions or lifecycle gates from module data.

## 4. Guardrail

The contract is enforced by:

```text
frontend/src/app/shell/ActionBar.test.tsx
frontend/tests/actionPatternContract.test.ts
```

The component test verifies dispatch, disabled reason, and running state. The
static contract blocks direct `available_actions.map` rendering inside module
views.

## 5. Next Extensions

Later slices can extend the same pattern with:

```text
- confirmation dialog support
- action grouping
- icon mapping by backend icon_key
- async result feedback
- download versus mutation handling by result_hint
```

Those extensions should continue consuming backend-owned action metadata.

Icon mapping must follow `GUI_BACKEND_OWNED_ICON_ASSET_REGISTRY.md`: action and
navigation icon keys are backend-owned metadata, while the frontend only maps an
approved key to an approved renderer or sanitized asset.
