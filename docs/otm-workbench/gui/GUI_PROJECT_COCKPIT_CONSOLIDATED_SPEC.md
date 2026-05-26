# GUI Project Cockpit Consolidated Specification

**Status:** draft for product review
**Date:** 2026-05-26
**Linear:** OTM-171
**Scope:** consolidated Project Cockpit objective, current UI review, browser
findings, GUI information architecture, route map, click-by-click operating
model, and redesign direction.

## 0. Source Documents Consolidated

This document consolidates the Project Cockpit direction currently spread across
GUI, shell, foundation, readiness, and shared component contracts:

```text
docs/otm-workbench/gui/GUI_PROJECT_COCKPIT_SUMMARY_CONTRACT.md
docs/otm-workbench/gui/GUI_SHELL_SCAFFOLD.md
docs/otm-workbench/gui/GUI_CONTEXT_SWITCHER.md
docs/otm-workbench/gui/GUI_CONTEXT_SUMMARY_PATTERN_CONTRACT.md
docs/otm-workbench/gui/GUI_READINESS_PANEL_PATTERN_CONTRACT.md
docs/otm-workbench/gui/GUI_MODULE_EXPERIENCE_ROADMAP.md
docs/otm-workbench/foundation/arquitetura_funcional_otm_workbench.md
docs/otm-workbench/foundation/arquitetura_tecnica_otm_workbench.md
```

Those files remain valid supporting evidence. This consolidated spec is the
current navigation point for future Project Cockpit UX and implementation work.

## 1. Product Objective

Project Cockpit should be the backend-first operational command center for the
active OTM Workbench project.

The module exists to help a project user answer:

```text
1. Which project/profile/environment/domain am I working in?
2. Is this context ready?
3. Which workstreams are ready, active, blocked, or not started?
4. What are the most important blockers?
5. What is the recommended next action?
6. Which recent jobs, artifacts, and evidence changed project state?
7. Which module should I open next?
8. Is the project prepared for CRP/cutover/handoff work?
```

Project Cockpit is not just a home page. It is the project-level decision and
navigation cockpit.

## 2. Core Story

The original backend contract is valid:

```text
active context
setup readiness
module summary
recent jobs
recent artifacts
recent evidence
available actions
```

The mature UX story should become:

```text
Confirm context -> inspect readiness -> review blockers -> choose next action
-> jump to the owning module -> return with updated project activity.
```

## 3. Explicit Non-Goals

Project Cockpit is not, for MVP0/MVP1:

```text
- a dashboard made of decorative metrics;
- a replacement for module detail screens;
- a frontend-owned readiness calculator;
- a permissions engine;
- a place to expose raw job input/result payloads;
- a raw artifact/evidence browser;
- a generic admin console;
- a landing page.
```

The backend remains the source of truth for active context, readiness, module
visibility, permissions, blockers, next actions, job safety, artifact safety,
evidence safety, and global cockpit actions.

## 4. Current UI Review

Browser review of `/home` found a clean and consistent first cockpit slice.

Delivered strengths:

```text
- shared shell and sidebar are consistent;
- backend-owned Project Cockpit summary endpoint is consumed;
- active context controls exist;
- setup readiness panel exists;
- visible module, recent job, artifact, and evidence metrics exist;
- recent jobs and recent evidence panels exist;
- global actions exist for setting context, viewing jobs, and viewing evidence;
- raw job input/result payloads, artifact file paths, and unsafe evidence
  summaries are not rendered.
```

Current product and UX problems:

1. The screen still feels like a basic home dashboard, not yet a command center.
2. The top actions (`Set active context`, `View jobs`, `View evidence`) are
   useful but not clearly prioritized by project state.
3. The active context selector appears even when context is already ready,
   taking a lot of prime space that could show readiness and next action.
4. Module summary is represented only by a count of visible modules. Users
   cannot see which workstream is ready, blocked, active, or needs attention.
5. There is no project-level "next best action" panel.
6. Blockers are not visible as first-class objects.
7. Recent artifacts count is shown, but artifacts are not listed.
8. Recent evidence can be empty for the active project, but the screen does not
   explain what that means or where to generate evidence.
9. There is no project readiness journey, milestone view, or module workstream
   status map.
10. There is no source-object/activity timeline across modules.

Product conclusion:

```text
The current Project Cockpit is a good backend contract proof and shell home
slice. It should not be treated as final UX. The next direction is a route-level
project operations cockpit centered on context, readiness, blockers, next
actions, workstream status, and recent proof.
```

## 5. Design Decision

Keep `/home` as the Project Cockpit hub, but turn it into a decision-oriented
control room with route-level drill-downs.

The new IA should be:

```text
/home
  Project Cockpit command center

/home/context
  Active context setup/switching

/home/readiness
  Project readiness and setup blockers

/home/workstreams
  Module/workstream status map

/home/blockers
  Cross-module blocker list

/home/activity
  Project activity timeline

/home/jobs
  Recent/background jobs for project context

/home/artifacts
  Recent project artifacts

/home/evidence
  Recent project evidence

/home/actions
  Global available actions and their readiness
```

Routes can be implemented incrementally. The key is that `/home` should stop
trying to be both context editor and operational overview at the same time.

## 6. Global UX Rules

1. Project Cockpit should prioritize decision support over decorative metrics.
2. The active context summary should be compact when ready and expanded only
   when setup is missing or the user opens `/home/context`.
3. Backend-owned next action should appear near the top of the screen.
4. Module/workstream statuses must be explicit, not hidden behind total counts.
5. Blockers must have owning module, severity, source object, and navigation.
6. Recent jobs, artifacts, and evidence must be client-safe and link to detail
   routes in their owning modules or Evidence Hub.
7. The frontend must not infer project readiness, module status, permission,
   blocker severity, or evidence safety.
8. No raw job payload, artifact local path, raw manifest, raw evidence payload,
   credential, or client-specific value should render.

## 7. Screen: `/home`

### Purpose

Give the user a quick operational answer:

```text
Where am I?
What is the state of the project?
What needs attention?
What should I do next?
```

### Backend Loads

```text
GET /api/v1/platform/project-cockpit/summary
GET /api/v1/platform/navigation
GET /api/v1/platform/preferences
```

### Main Content

```text
- compact active context summary;
- setup/readiness banner;
- backend-owned next action panel;
- project health/workstream map;
- blockers needing attention;
- recent jobs, artifacts, and evidence;
- global available actions.
```

### Clicks

| Click | Opens |
|---|---|
| `Change context` | `/home/context` |
| readiness banner | `/home/readiness` |
| next action | backend-provided route |
| workstream row/card | owning module route or `/home/workstreams` |
| blocker row | owning module/source object route |
| recent job row | `/home/jobs` or Admin jobs detail |
| recent artifact row | Evidence Hub artifact detail |
| recent evidence row | Evidence Hub evidence detail |
| `View all activity` | `/home/activity` |

### What Must Not Be Here

```text
- full context setup form when context is already ready;
- raw job input/result payloads;
- artifact file paths;
- evidence raw summary_json;
- long module detail tables;
- admin setup controls unrelated to the current next action.
```

## 8. Screen: Active Context

### Route

```text
/home/context
```

### Purpose

Select or switch project/profile/environment/domain with backend-owned
validation and feedback.

### Backend Loads

```text
GET /api/v1/platform/projects
GET /api/v1/platform/projects/{project_id}/profiles
GET /api/v1/platform/projects/{project_id}/environments
GET /api/v1/platform/active-context
GET /api/v1/platform/active-context/capabilities
```

### Actions

| Action | Backend execution | Result |
|---|---|---|
| `Apply context` | backend active-context update | returns to `/home` with refreshed summary |
| `Reset draft` | local reset from backend active context | draft clears |
| `Cancel` | none | back to `/home` |

### States

```text
- no project available;
- project selected, profile missing;
- environment missing;
- domain invalid;
- context ready;
- context update denied by permission.
```

## 9. Screen: Project Readiness

### Route

```text
/home/readiness
```

### Purpose

Explain setup readiness, blockers, and next setup actions.

### Backend Loads

```text
GET /api/v1/platform/project-cockpit/summary
GET /api/v1/platform/project-cockpit/readiness
```

### Main Content

```text
- setup status;
- readiness checks;
- blockers grouped by severity;
- owning module/source object;
- recommended next action;
- evidence/artifact references proving readiness.
```

## 10. Screen: Workstreams

### Route

```text
/home/workstreams
```

### Purpose

Show module/workstream status as project journeys, not only navigation links.

### Backend Loads

```text
GET /api/v1/platform/project-cockpit/module-summary
GET /api/v1/platform/modules
```

### Workstream Examples

```text
Project setup
Master Data / Data Factory
Rates
Load Plan / Cutover
Evidence Hub
Assets Library
Integration Mapping
Order Release Generator
Catalog Core
Admin / Jobs
```

### Row Data

```text
- status;
- summary;
- blockers;
- recent activity;
- next action;
- owning route;
- last evidence/artifact.
```

## 11. Screen: Blockers

### Route

```text
/home/blockers
```

### Purpose

List cross-module blockers that stop project progress.

### Backend Loads

```text
GET /api/v1/platform/project-cockpit/blockers?filters...
```

### Clicks

| Click | Opens |
|---|---|
| blocker row | owning module/source route |
| evidence/artifact reference | Evidence Hub route |
| module filter | updates backend query |

Blockers must be backend-owned. The frontend should only render severity,
message, owner, route, and disabled reasons.

## 12. Screen: Activity Timeline

### Route

```text
/home/activity
```

### Purpose

Show a project-level timeline across jobs, artifacts, evidence, module actions,
and readiness changes.

### Backend Loads

```text
GET /api/v1/platform/project-cockpit/activity?filters...
```

### Main Content

```text
- timeline grouped by day/module;
- recent jobs;
- generated artifacts;
- generated evidence;
- readiness changes;
- archive package creation;
- guarded links to source objects.
```

Raw job input/result payloads and raw evidence payloads must never render.

## 13. Screen: Jobs

### Route

```text
/home/jobs
```

### Purpose

Show recent project jobs as operational signals, not admin internals.

### Backend Loads

```text
GET /api/v1/platform/project-cockpit/jobs?filters...
```

### Main Content

```text
- job code/name;
- source module;
- status;
- started/finished;
- input_present/result_present only;
- source object route;
- evidence/artifact generated.
```

Full job administration remains in Admin Console.

## 14. Screen: Artifacts

### Route

```text
/home/artifacts
```

### Purpose

Show recent project artifacts as a quick operational list.

Artifact detail and downloads should route to Evidence Hub, not be implemented
locally inside Project Cockpit.

## 15. Screen: Evidence

### Route

```text
/home/evidence
```

### Purpose

Show recent client-safe evidence in project context.

Evidence detail should route to Evidence Hub.

## 16. Screen: Global Actions

### Route

```text
/home/actions
```

### Purpose

Render backend-owned global cockpit actions and explain why each is available or
blocked.

### Action Examples

```text
Set active context
Review project readiness
Open next blocker
Open Load Plan readiness
Open Evidence Hub
Open Admin jobs
```

Actions must come from backend `available_actions` or a cockpit action contract.

## 17. Backend Contract Gaps

The current backend summary contract is a good foundation. Route-level UX needs
explicit contracts or extensions for:

```text
GET /api/v1/platform/project-cockpit/readiness
GET /api/v1/platform/project-cockpit/module-summary
GET /api/v1/platform/project-cockpit/blockers
GET /api/v1/platform/project-cockpit/activity
GET /api/v1/platform/project-cockpit/jobs
GET /api/v1/platform/project-cockpit/artifacts
GET /api/v1/platform/project-cockpit/evidence
GET /api/v1/platform/project-cockpit/actions
```

Where these are already represented inside `/summary`, the GUI may consume the
summary until separate contracts exist. It must not infer readiness locally.

## 18. QA Journeys

Required browser/UI QA:

```text
1. open cockpit with no active project and confirm setup next action;
2. select project/profile/environment/domain and apply context;
3. reload cockpit and confirm context persists from backend;
4. open readiness and navigate to a blocker owner;
5. open workstreams and navigate to a module next action;
6. open recent job and confirm raw input/result is not shown;
7. open recent artifact and route to Evidence Hub artifact detail;
8. open recent evidence and route to Evidence Hub evidence detail;
9. switch context and confirm jobs/artifacts/evidence/readiness refresh;
10. verify no raw payload, local path, credential, CNPJ, CPF, or production
    identifier appears.
```

Visual QA:

```text
- desktop and mobile route fit;
- context ready and context missing states;
- empty recent jobs/artifacts/evidence states;
- blocked project readiness state;
- high-volume module/workstream list;
- long project/profile/environment labels;
- light/dark/system theme and compact density.
```

## 19. Implementation Slices

Recommended implementation order:

```text
1. Compact `/home` layout with next action, readiness, workstream status, and
   recent proof panels.
2. `/home/context` route for active context switching.
3. `/home/readiness` route for setup blockers.
4. `/home/workstreams` route for module status.
5. `/home/activity` route for project timeline.
6. `/home/blockers` route when backend blocker contract exists.
7. `/home/jobs`, `/home/artifacts`, and `/home/evidence` quick lists that link
   to owning detail routes.
8. Browser QA for context switch, route return, empty states, and blocked states.
```

## 20. Acceptance Criteria

Project Cockpit can be considered product-ready when:

```text
- the user can understand context, readiness, blockers, next action, and recent
  proof within one screen;
- context setup is clear but does not dominate the screen when already ready;
- module/workstream status is visible beyond a total module count;
- blockers and next actions navigate to the owning module/source object;
- jobs, artifacts, and evidence are client-safe and link to detail routes;
- frontend does not calculate readiness, permissions, blocker severity, or
  evidence safety;
- docs, tests, Linear, and GitHub point to this spec.
```

## 21. Decision Summary

The current Project Cockpit should remain as backend summary evidence, not final
UX. The next direction is a route-level command center:

```text
Context -> readiness -> blockers -> next action -> workstreams -> activity ->
recent jobs/artifacts/evidence.
```

This keeps the cockpit backend-first while making it the place where the user
knows what to do next.

