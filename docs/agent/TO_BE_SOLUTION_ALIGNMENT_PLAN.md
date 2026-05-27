# To-Be Solution Alignment Plan

**Status:** active planning baseline
**Date:** 2026-05-27

## Goal

Move OTM Workbench from the current broad frontend/backend implementation to
the validated To-Be experience captured in the Complete Solution Mockup, while
preserving backend capabilities that support active modules and avoiding
destructive cleanup.

## Active To-Be Visual Source

```text
OTM Workbench - Complete Solution Mockup
https://www.figma.com/design/7AkORIWrjmaOiBBA6cMOj9/OTM-Workbench---Complete-Solution-Mockup
Page: 00 Analysis + Visual System
Boards: 10 through 16 deep-flow boards
```

Supporting artifacts:

- `docs/agent/figma-wireframes/OTM_WORKBENCH_COMPLETE_SOLUTION_DEEP_FLOW_REPORT.md`
- `docs/agent/figma-wireframes/OTM_WORKBENCH_AS_IS_SOLUTION_DIAGRAMS_REPORT.md`
- module scope reviews under `docs/agent/module-scope/`
- Michelangelo wireframe briefs under `docs/agent/wireframe-briefs/`
- GUI specs under `docs/otm-workbench/gui/`

## Delivery Order

The active implementation order is:

1. Frontend cleanup and current-phase navigation pruning.
2. Client/domain and environment segregation foundation.
3. Settings to completion.
4. Cockpit to completion.
5. Rates Studio.
6. Assets Library.
7. Master Data / Data Factory.
8. Integration Mapping Studio.
9. Order Release Generator.

Load Plan remains in the active UI phase and should be preserved as a
cross-module cutover/package dependency, but the next focused delivery sequence
starts with the modules above unless the user reprioritizes it.

## Slice 1: Frontend Cleanup And Navigation Pruning

Objective:

Keep only the current active UI phase visible in the main navigation and
Cockpit launch surfaces while preserving internal/backend dependencies.

Initial code areas to inventory before editing:

- `frontend/src/app/routes/WorkbenchRoute.tsx`
- `frontend/src/modules/index.ts`
- `frontend/src/app/routes/moduleDescriptions.ts`
- `frontend/src/app/App.test.tsx`
- `frontend/src/app/AppFunctional*.test.tsx`
- `frontend/scripts/functional-*-browser.mjs`
- backend navigation source under `src/otm_workbench/platform/navigation.py`

Current cleanup candidates:

- hide or remove top-level frontend exposure for Catalog Core;
- hide or remove top-level frontend exposure for Evidence Hub;
- hide or remove separate Admin Console / Jobs exposure;
- hide or remove Developer Tools from normal navigation;
- hide or remove Coordinate Quality as standalone exposure if present;
- keep Catalog/Data Dictionary, evidence, jobs, and restricted diagnostics as
  internal dependencies where active modules need them.

Acceptance criteria:

- main navigation exposes only Cockpit, Settings, Rates, Assets, Master Data,
  Load Plan, Integration, and Order Release;
- out-of-current-phase routes are not visible to normal users;
- route recovery is explicit for stale links;
- tests are adjusted to distinguish hidden UI from retained backend capability;
- no source module is deleted without separate approval.

## Slice 2: Client/Domain And Environment Segregation

Objective:

Make `client/domain`, `environment`, and visibility/access policy explicit
across operational records, APIs, UI context, tests, and generated artifacts.

Planning requirements:

- identify every persistence model that represents operational data;
- classify which records require `client_domain_id`, `environment_id`, and
  visibility/access-policy scope;
- define migration/backfill behavior for synthetic local data;
- require query filtering by active context for normal users;
- define `DBA` override behavior and audit visibility;
- ensure Public View is a separate shared scope, not a private-data bypass.

Acceptance criteria:

- every operational create/update path receives explicit context;
- every list/detail path filters by allowed scope unless the user is `DBA`;
- generated artifacts and evidence carry scope metadata;
- tests prove cross-client and cross-environment isolation;
- fixtures contain only synthetic scoped data.

## Slice 3: Settings To Completion

Objective:

Finish Settings as the setup and access-control module for the current UI
phase.

Required flows:

- Settings hub;
- setup library search;
- project detail;
- client/domain setup;
- environment detail;
- profiles;
- users;
- user detail;
- roles matrix;
- grant editor;
- access policies;
- policy review;
- permission denied;
- audit search;
- audit no results;
- route recovery.

Completion gates:

- backend API contracts;
- route-level UI screens or deliberate modals;
- permission gates;
- audit evidence;
- tests for allowed, denied, expired, DBA, Public View, and stale-route states.

## Slice 4: Cockpit To Completion

Objective:

Finish Cockpit as the user's entry point for login/session recovery, context
selection, accelerator launch, Public View entry, project info, and scoped
visibility.

Required flows:

- login;
- session ended;
- cockpit home;
- context selector;
- Public View scope;
- no-context blocked state;
- accelerator launcher;
- module permission state;
- project info;
- secure vault placeholder;
- user menu;
- theme toggle;
- DBA visibility;
- Settings boundary;
- Public/private switch guard;
- route recovery.

Completion gates:

- no readiness/workstream/jobs dashboard behavior;
- every accelerator launch checks context and permission;
- stale context and stale routes recover safely;
- Public View never leaks private data.

## Later Module Revalidation Gate

Before each module implementation slice begins, revalidate:

- desired user outcome;
- primary object lifecycle;
- active Figma deep-flow screens;
- module scope review;
- wireframe brief;
- GUI source spec;
- backend/API readiness;
- required fixture files;
- OTM Data Dictionary and Oracle documentation dependencies;
- positive, negative, out-of-order, permission, route-recovery, and generated
  artifact test scenarios.

## GitHub Visibility

GitHub Issues, PRs, and Actions should be updated when a delivery slice changes
product behavior or creates an approved implementation plan. This planning slice
records the direction in repo docs first. The next execution slice should
create or update GitHub issue/PR records with links to this plan. Linear is
historical/paused unless explicitly reactivated.
