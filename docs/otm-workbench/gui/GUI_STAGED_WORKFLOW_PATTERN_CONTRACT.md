# GUI Staged Workflow Pattern Contract

**Status:** delivered
**Scope:** guardrail for complex module screens that need a clear operational story instead of stacked, disconnected panels.

## 1. Purpose

Complex modules must guide the user through a workflow. They must not expose
every authoring form, list, action, and operational panel at once.

This matters most for modules such as Integration Mapping Studio, Master Data,
Cutover, Order Release Generator, and any future module where the user builds an
object through ordered decisions.

## 2. Rule

When a screen has multiple authoring surfaces, use a staged workflow.

```text
- One primary operational stage is visible at a time.
- The stage order must follow the real user story.
- Side panels may preserve selected-object context and backend actions.
- Users can move between stages without losing backend-owned state.
- Manual fallback fields may exist, but they must live inside the relevant stage.
- Do not stack unrelated OperationalPanel sections one after another.
```

## 3. Backend Ownership

The staged workflow is a presentation pattern only.

The frontend must not invent lifecycle gates that conflict with backend
contracts. Backend remains source of truth for readiness, validation,
permissions, available actions, generated artifacts, evidence, and object
status.

## 4. Expected Screen Shape

Use this shape for complex modules:

```text
PageHeader
MetricGrid
ModuleWorkspaceLayout
  Primary area
    Staged workflow navigation
    Current stage panel
  Side area
    SelectedObjectPanel with context, actions, artifacts, evidence, blockers
```

## 5. Current Enforcement

Integration Mapping Studio uses this contract:

```text
1. Systems & endpoints
2. Definition
3. Payloads & schemas
4. Mapping rules
5. Definitions list
```

`AppFunctionalIntegrationMapping.test.tsx` verifies that only one primary
operational authoring stage is rendered at a time.
