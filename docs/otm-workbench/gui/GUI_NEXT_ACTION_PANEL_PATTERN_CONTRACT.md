# GUI Next Action Panel Pattern Contract

**Status:** first slice delivered  
**Linear:** `OTM-142`  
**Scope:** shared panel that tells the user what object is selected, what stage
is active, what the next backend-owned action is, and why it is blocked.

## 1. Purpose

Staged module screens must not force the user to infer the next useful action
from a row of workflow steps.

`NextActionPanel` is the shared GUI pattern for the first-viewport question:

```text
Where am I?
What object am I working on?
What is the next action?
Why is it blocked, if blocked?
```

## 2. Ownership

The panel renders guidance. It must not become an independent workflow engine.

Backend remains source of truth for:

```text
- available action labels
- disabled state
- disabled reason
- recommended action flags
- object lifecycle state
- validation and permission blockers
```

When a module already exposes `available_actions`, the panel must prefer the
recommended non-disabled action, then the first available action, then the first
blocked action.

When a module does not yet expose `available_actions`, the panel may use the
module's backend-returned objects and durable state as a temporary first slice,
but that logic must stay small and be replaced by backend action contracts when
available.

## 3. Delivered First Slice

```text
Component: frontend/src/ui/components/nextAction.tsx
Style: frontend/src/ui/layouts.css
Tests: frontend/src/ui/components.test.tsx
Applied modules: Data Factory, Load Plan, and Integration Mapping
```

Data Factory uses template and batch `available_actions`.

Load Plan uses package/checklist/readiness/export state until a dedicated
backend action contract is exposed for cutover packages.

Integration Mapping uses selected definition, payload/schema, mapping,
validation, preview/spec, and generated artifact state until a dedicated
backend action contract is exposed for mapping definitions.

## 4. Interaction Rules

```text
- Use one panel immediately after staged workflow navigation.
- Keep the title compact: "Next action".
- Show selected object label/value and active stage.
- Show one primary action label and a status chip.
- Show backend disabled reason as a blocker, not as hidden tooltip-only text.
- Keep the panel informational; execution still happens through the module's
  normal action buttons.
```

## 5. Acceptance

```text
- Component test covers ready and blocked guidance.
- Module functional tests assert the first useful action is visible.
- The panel must not introduce extra business decisions into UI-only code.
- Future modules should reuse the shared component rather than introducing a
  page-specific recommendation banner.
```
