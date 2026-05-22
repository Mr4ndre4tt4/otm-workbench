# GUI Module Experience Architecture

**Status:** accepted baseline
**Linear:** GUI planning checkpoint after `OTM-96`
**Scope:** module-level screen storytelling, reusable experience patterns, and backend-first GUI boundaries.

## 1. Purpose

OTM Workbench modules must feel like one product even when their domains are
different.

This contract defines how module screens should be composed before any new
module work starts. It prevents disconnected screens where several forms,
lists, panels, and actions are stacked without a clear operational story.

## 2. Core Rule

Every module screen needs one primary story.

```text
What object is the user working on?
What stage of work are they in?
What decision or action is expected next?
What backend-owned state proves the action happened?
```

If a screen cannot answer those questions, it should not gain more panels. It
needs a clearer experience pattern.

## 3. Experience Layers

Module GUI work is planned in three layers.

```text
1. Workbench shell
   Session, navigation, active context, theme, density, sidebar, global status,
   and route frame.

2. Module experience pattern
   Overview, object list/detail, staged workflow, tabbed detail, review queue,
   artifact/evidence/jobs surface, or dashboard.

3. Module-specific exception
   Schema tree, mapping designer, XML/JSON preview, CSV preview table, load
   sequence graph, coordinate map, or another domain interaction approved in
   GUI_EXCEPTIONS_REGISTER.md.
```

The shell and shared patterns come first. Exceptions are added only when the
standard patterns cannot explain the work.

## 4. Pattern Selection

Use this decision table before building a module route.

| Need | Pattern | Rule |
|---|---|---|
| Show health, recent objects, blockers, recent artifacts | Module overview | First screen for a mature module. |
| Select one object and inspect backend-owned metadata | Object list/detail | Default for most MVP0 module screens. |
| Build one object through ordered authoring steps | Staged workflow | Show one primary stage at a time. |
| Inspect a complete object from several stable angles | Tabbed detail | Use when the object already exists and the user is reviewing it. |
| Resolve validation findings, blockers, or readiness decisions | Review queue | Use severity/category/status/evidence-oriented rows. |
| Show generated files, evidence, jobs, or audit | Operational surface | Use shared ArtifactList, ActivityRow, BlockerPanel, and OperationalPanel. |
| Need visual mapping, tree, preview, or graph interaction | Documented exception | Keep the exception inside the module, but reuse shell/actions/states. |

## 5. Storytelling Rules

Module screens must avoid the "everything at once" layout.

```text
- Do not stack unrelated authoring forms one below another.
- Do not mix setup, object authoring, review, and generated outputs as equal
  panels in a single scroll.
- Do not create decorative sections to make a page look fuller.
- Do not make a dashboard if the user needs to perform an operational workflow.
- Do not hide primary workflow state only in local frontend state.
```

Instead, compose screens as:

```text
PageHeader
MetricGrid or context summary
Primary workspace pattern
Selected object side panel
Operational surface or blockers, when backed by API contracts
```

The primary workspace owns the story. The side panel provides context, safe
metadata, and backend-owned actions. Operational surfaces show jobs, artifacts,
evidence, blockers, and audit facts after the backend exposes them.

## 6. Backend Ownership

Frontend may guide the user, but it does not decide product truth.

Backend remains authoritative for:

```text
- navigation and module visibility
- permissions and capabilities
- lifecycle and readiness
- available actions and disabled reasons
- validation and OTM dependency decisions
- jobs, progress, artifacts, evidence, audit
- generated file ownership and download eligibility
- active context and user preferences
```

Frontend owns:

```text
- layout and responsive composition
- local selection and current visible stage
- accessible labels and keyboard behavior
- loading, empty, error, warning, success, blocked, disabled, and read-only
  rendering
- mapping backend payloads into shared component props
```

Frontend may disable a submit button for missing local form input, but it must
not infer lifecycle eligibility, permission eligibility, OTM dependency
validity, artifact ownership, or readiness.

## 7. Module Archetypes

Initial module archetypes:

| Module | Primary pattern | Notes |
|---|---|---|
| Project Cockpit | Module overview | Decision-oriented summary, active context, readiness, recent activity. |
| Rates Studio | Object list/detail plus operational surfaces | Batch lifecycle, blockers, CSV artifacts, evidence, approval. |
| OTM Catalog Core | Object list/detail | Search/validate tables, columns, references, dependencies. |
| Data Factory / Master Data | Staged workflow plus object detail | Template selection, workbook, validation, mapping, output artifacts. |
| Load Plan / Cutover | Review queue plus staged workflow | Package registration, checklist, readiness, go/no-go, handoff. |
| Assets Library | Object list/detail | Asset metadata, versions, links, guarded downloads. |
| Evidence Hub | Object list/detail plus operational surfaces | Evidence discovery, archive packages, guarded downloads. |
| Order Release Generator | Staged workflow | Template, input rows, XML preview, artifact generation, guarded submit. |
| Integration Mapping Studio | Staged workflow | Systems, definition, payload/schema, rules, validation, spec artifacts. |
| Admin Console | Tabbed detail and setup workflows | Workspace, project, profile, environment, users, roles, flags, jobs, audit. |

These archetypes can evolve only through an updated decision or exception entry.

## 8. Theme, Density, And Icons

The experience architecture must work in light, dark, and system modes.

```text
- Light mode is default.
- Theme, density, and sidebar preferences are backend-owned.
- Module screens consume semantic tokens, not module palettes.
- Icons use the governed shared icon family.
- Icon family changes must be system-wide, not per module.
- Dark mode icons and controls use currentColor/tokens, not separate local
  assets unless a design-system exception is approved.
```

## 9. Desktop-Ready Boundary

The first GUI is browser-first, but module screens must stay desktop-ready.

```text
- No direct desktop APIs inside module views.
- Heavy local engines are called through backend/local service contracts.
- File repositories, templates, and collaborative assets stay behind backend
  APIs or platform adapters.
- A future desktop wrapper should be able to reuse module routes and backend
  contracts.
```

## 10. QA Gate

A module experience is not complete until the following are true:

```text
- The chosen pattern is documented.
- The primary workflow has a functional QA journey.
- The browser journey proves route return-state from backend-owned data.
- Visual/responsive QA checks no overlap and no disconnected stacked panels.
- Accessibility covers stage navigation, selected object, actions, and
  artifacts/jobs/evidence when present.
- Linear has delivered scope, validations, and follow-up gaps.
```

If the screen is dense, visual QA must include at least one desktop and one
mobile viewport before the module is considered GUI-ready.

## 11. Implementation Rule

Before adding or changing a module screen:

```text
1. Pick the module archetype.
2. Pick one primary experience pattern.
3. Identify the backend contracts used by the story.
4. Identify which states/actions remain backend-owned.
5. Reuse shared UI kit components.
6. Register exceptions before adding custom interactions.
7. Add or update functional and visual QA coverage.
8. Update GUI docs and Linear.
```

If a module needs more than one primary story, split it into routes, tabs, or
stages. Do not place independent screens one below another.
