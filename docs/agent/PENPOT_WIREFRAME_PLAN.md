# Penpot Wireframe Plan

**Status:** supporting historical plan
**Date:** 2026-05-27

## Current Notice

The current active To-Be visual target is the Complete Solution Mockup, not
this Penpot queue:

```text
OTM Workbench - Complete Solution Mockup
https://www.figma.com/design/7AkORIWrjmaOiBBA6cMOj9/OTM-Workbench---Complete-Solution-Mockup
active page: 00 Analysis + Visual System
```

The previous Figma consolidation file remains supporting evidence:

```text
OTM Workbench - Consolidated Scope Wireframes
https://www.figma.com/design/zJGLRJCTArRStISGIPQ2DQ
supporting page: Current Scope v2 - Prototype DNA
```

For the current UI phase, only Cockpit, Master Data, Rates, Load Plan,
Integration, Order Release, Assets, and Settings remain in the top-level UI.
Catalog Core, Evidence Hub, separate Admin Console / Jobs, Developer Tools, and
Coordinate Quality as a top-level module are out of the main UI for now.

This Penpot plan is retained as historical/supporting context for the earlier
Penpot cockpit passes and broad module wireframe plan.

## Purpose

Create wireframes and mockups for OTM Workbench modules from validated module
scope and specs. The goal is not to recreate the current UI in Penpot. The goal
is to define the target product experience before cleanup and development.

## Penpot Target

```text
https://design.penpot.app/#/workspace?team-id=e7a86fff-661d-81c1-8008-148fafe68f60&file-id=e7a86fff-661d-81c1-8008-14af24af603d&page-id=e7a86fff-661d-81c1-8008-14af24af603e
```

## Inputs Per Module

- validated row in `MODULE_SCOPE_LEDGER.md`;
- current consolidated module spec;
- backend/API contract notes;
- module acceptance criteria;
- Michelangelo UX brief;
- known QA findings and route recovery requirements.

## Michelangelo Brief Template

```text
Module:
Primary user:
Primary task:
Task criticality:
Primary object:
Route family:
Screen archetypes:
Happy path:
Negative path:
Out-of-order path:
Route recovery path:
Blocked states:
Empty/loading/error/success states:
Backend-owned labels/actions/status:
Accessibility risks:
Acceptance criteria:
```

## Penpot Structure

Recommended execution order:

1. Shell / Project Cockpit, including login and logout/session recovery.
2. Master Data / Data Factory.
3. Coordinate Quality, as Master Data / Quality Tools scope.
4. Rates Studio.
5. Load Plan / Cutover.
6. Integration Mapping Studio.
7. Assets Library.
8. Catalog Core.
9. Evidence Hub.
10. Order Release Generator.
11. Admin Console / Jobs.
12. Developer Tools.

Recommended pages:

- `00 Governance`
- `01 Shell, Login, Logout, and Project Cockpit`
- `02 Master Data`
- `03 Coordinate Quality`
- `04 Rates Studio`
- `05 Load Plan and Cutover`
- `06 Integration Mapping`
- `07 Assets Library`
- `08 Catalog Core`
- `09 Evidence Hub`
- `10 Order Release Generator`
- `11 Admin Console`
- `12 Developer Tools`

Coordinate Quality may use a separate Penpot page for review clarity, but it
remains part of the Master Data / Quality Tools product scope unless a future
decision promotes it to a standalone module.

## Current Penpot Build Queue

| Order | Module | Build packet | Penpot status |
|---|---|---|---|
| 1 | Shell / Login / Logout / Project Cockpit | `docs/agent/penpot-wireframes/PROJECT_COCKPIT_V3_WIREFRAME_BLUEPRINT.json` | V3 created; old v1/v2.1 generated boards removed from Penpot; ready for Michelangelo/user visual review |

Recommended frame types per module:

- journey map;
- route map;
- hub screen;
- list/library screen;
- detail screen;
- create/edit/copy/delete or retire screens;
- workflow screen;
- login/logout/session recovery screens where applicable;
- blocked/error states;
- mobile/responsive check where needed.

Project Cockpit v3 frame set:

- navigation map;
- login;
- logout/session ended;
- single Project Cockpit with Context Selector, Project Info, and Accelerators.

Recommended frame naming:

```text
<MODULE>-<NUMBER> <Screen Name>
```

Examples:

```text
SHELL-01 Login
SHELL-02 Logout Confirmed
MD-01 Hub
MD-02 Data Factory
CAT-03 Table Detail
```

State frames should use suffixes:

```text
empty
blocked
error
success
mobile
```

## Acceptance Gate

A module can move from Penpot to cleanup planning only when:

- all required routes have wireframes;
- primary actions and return paths are visible;
- login/logout/session states are represented for Shell work;
- happy, negative, out-of-order, and recovery paths are represented;
- Michelangelo findings are either resolved or explicitly accepted as risk;
- the user validates the module mockups.

## Visual Approval Criteria

Each module wireframe is ready for mockup only when it shows:

- route entry;
- primary object;
- primary action;
- visible return path;
- empty state;
- blocked/error state;
- success or completed state where relevant;
- out-of-order or recovery path;
- backend-owned labels/actions/status placeholders.
