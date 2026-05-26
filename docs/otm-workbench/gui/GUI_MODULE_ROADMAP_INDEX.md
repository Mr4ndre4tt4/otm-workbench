# GUI Module Roadmap Index

**Status:** active index
**Date:** 2026-05-26
**Scope:** module-by-module roadmap entry point for GUI/product specs, module
views, QA evidence, and next documentation gaps.

## 1. Purpose

This file is the navigation index for module roadmaps.

`GUI_MODULE_EXPERIENCE_ROADMAP.md` remains the narrative roadmap. This index
keeps each module discoverable and points to the most specific module document
available. When a module needs a deeper click-by-click redesign like Master
Data, the new module-specific spec should be added here.

## 2. Index Rules

Every module should have, in order of preference:

1. a module-specific UX/product spec with route map, screens, clicks, actions,
   backend contracts, QA criteria, and non-goals;
2. a module view contract when the screen already exists but does not yet have
   a full redesign spec;
3. QA/review evidence for what has already been tested;
4. a clear next documentation gap.

Module specs must preserve the project rules:

- backend-owned state, labels, available actions, permissions, preferences,
  menu metadata, templates, and validation rules;
- no real client data in docs, fixtures, screenshots, or seeds;
- route-level detail screens for complex objects and destructive actions;
- one primary task per screen;
- visible `Back` action on drill-down, edit, copy, delete/retire, and result
  screens;
- functional QA must test happy path, negative path, out-of-order path, and
  route leave/return recovery.

## 3. Module Roadmap Matrix

| Module | Current specific doc | Supporting docs | Current doc status | Next documentation action |
|---|---|---|---|---|
| Shell / Project Cockpit | `GUI_PROJECT_COCKPIT_CONSOLIDATED_SPEC.md` | `GUI_SHELL_SCAFFOLD.md`, `GUI_PROJECT_COCKPIT_SUMMARY_CONTRACT.md`, `GUI_AUTH_SESSION_FLOW.md`, `GUI_CONTEXT_SWITCHER.md`, `GUI_THEME_PREFERENCES.md` | Consolidated objective, current MVP evidence, browser findings, and click-by-click redesign spec exists; current summary contract remains backend evidence. | Use the consolidated spec before major Project Cockpit UI implementation changes. |
| Rates Studio | `GUI_RATES_STUDIO_CONSOLIDATED_SPEC.md` | `GUI_RATES_SUMMARY_VIEW.md`, `GUI_RATES_BATCH_DETAIL_PANEL.md`, `GUI_RATES_ACTION_EXECUTION.md`, `GUI_RATES_ARTIFACT_DOWNLOAD.md`, `GUI_RATES_ARTIFACTS_EVIDENCE.md`, `GUI_RATES_MVP_COMPLETION_REVIEW_OTM58.md`, `GUI_RATES_VISUAL_QA_OTM78.md` | Consolidated objective, MVP evidence, browser findings, and click-by-click redesign spec exists; current MVP view remains contract evidence. | Use the consolidated spec before major Rates UI implementation changes. |
| OTM Catalog Core | `GUI_CATALOG_CORE_VIEW.md` | `GUI_MODULE_API_CONTRACT_MATRIX.md`, `GUI_MODULE_RECONCILIATION_COMPLETION_REVIEW_OTM86.md` | View contract exists. | Create `GUI_CATALOG_CORE_ROADMAP_SPEC.md` when adding table/detail/search authoring flows. |
| Load Plan / Cutover | `GUI_LOAD_PLAN_CUTOVER_CONSOLIDATED_SPEC.md` | `GUI_LOAD_PLAN_VIEW.md`, `GUI_FUNCTIONAL_QA_JOURNEYS.md`, `GUI_GENERAL_SOLUTION_QA_2026_05_25.md` | Consolidated objective, MVP evidence, browser findings, and click-by-click redesign spec exists; current MVP view remains contract evidence. | Use the consolidated spec before major Load Plan / Cutover UI implementation changes. |
| Master Data / Data Factory | `GUI_MASTER_DATA_DATA_FACTORY_REDESIGN_SPEC.md` | `GUI_MASTER_DATA_VIEW.md`, `GUI_MASTER_DATA_COMPLETION_REVIEW_OTM115.md`, `GUI_MASTER_DATA_MVP_WORKFLOW_REVIEW_OTM119.md`, `output/gui-qa/master-data/` | Full click-by-click redesign spec exists; Slice 1 hub/route-family separation and Slice 2A route-level template detail are delivered with React and browser QA evidence. | Continue Slice 2B: route-level batch detail and clearer operational action placement. |
| Coordinate Quality / Lat-Lon | `GUI_MASTER_DATA_DATA_FACTORY_REDESIGN_SPEC.md` | `GUI_MASTER_DATA_VIEW.md` | Covered as `Quality Tools` under Master Data redesign. | Create a separate `GUI_COORDINATE_QUALITY_ROADMAP_SPEC.md` only if it becomes a standalone module. |
| Evidence Hub | `GUI_EVIDENCE_HUB_CONSOLIDATED_SPEC.md` | `GUI_EVIDENCE_HUB_VIEW.md`, `GUI_GENERAL_SOLUTION_QA_2026_05_25.md` | Consolidated objective, current MVP evidence, browser findings, and click-by-click redesign spec exists; current MVP view remains contract evidence. | Use the consolidated spec before major Evidence Hub UI implementation changes. |
| Assets Library | `GUI_ASSETS_LIBRARY_CONSOLIDATED_SPEC.md` | `GUI_ASSETS_LIBRARY_VIEW.md`, `GUI_GENERAL_SOLUTION_QA_2026_05_25.md` | Consolidated objective, MVP evidence, browser findings, and click-by-click redesign spec exists; current MVP view remains contract evidence. | Use the consolidated spec before major Assets Library UI implementation changes. |
| Order Release Generator | `GUI_ORDER_RELEASE_GENERATOR_CONSOLIDATED_SPEC.md` | `GUI_ORDER_RELEASE_GENERATOR_VIEW.md`, `GUI_GENERAL_SOLUTION_QA_2026_05_25.md` | Consolidated objective, current MVP evidence, browser findings, and click-by-click redesign spec exists; current MVP view remains contract evidence. | Use the consolidated spec before major Order Release Generator UI implementation changes. |
| Integration Mapping Studio | `GUI_INTEGRATION_MAPPING_CONSOLIDATED_SPEC.md` | `GUI_INTEGRATION_MAPPING_VIEW.md`, `GUI_INTEGRATION_MAPPING_NDD_UI_QA.md`, `GUI_INTEGRATION_MAPPING_VISUAL_QA_OTM79.md`, `GUI_LOCAL_INTEGRATION_VALIDATION.md` | Consolidated objective, current MVP evidence, browser findings, and click-by-click redesign spec exists; current MVP view remains contract evidence. | Use the consolidated spec before major Integration Mapping UI implementation changes. |
| Admin Console / Jobs | `GUI_ADMIN_CONSOLE_CONSOLIDATED_SPEC.md` | `GUI_MODULE_API_CONTRACT_MATRIX.md`, `GUI_GENERAL_SCREEN_PASS_2026_05_26.md` | Consolidated objective, current browser findings, and click-by-click route-level administration spec exists. | Use the consolidated spec before expanding setup, users/roles, feature flags, jobs, audit, OTM connections, or module governance UI. |
| Developer Tools | `GUI_DEVELOPER_TOOLS_CONSOLIDATED_SPEC.md` | `GUI_BROWSER_RUNTIME_DIAGNOSTIC.md`, `GUI_BROWSER_QA_ATTEMPT.md`, `GUI_MODULE_API_CONTRACT_MATRIX.md` | Consolidated objective, current placeholder/browser findings, route-level controlled technical tools spec exists. | Use the consolidated spec before exposing any real Developer/DBA tool beyond the guarded placeholder. |
| Backend-Owned Icon / Asset Registry | `GUI_BACKEND_OWNED_ICON_ASSET_REGISTRY.md` | `GUI_DESIGN_SYSTEM_HANDOFF.md`, `GUI_COMPONENT_GALLERY_PLAN.md` | Backend-facing contract exists. | Link each module spec to this registry when defining sidebar icons, labels, empty-state assets, and status visuals. |

## 4. Spec Template For New Module Roadmaps

New module-specific specs should follow this minimum structure:

```text
# GUI <Module Name> Roadmap Specification

Status / Date / Scope
1. Problem Statement
2. Design Decision
3. Core Navigation Map
4. Global UX Rules
5. Screen-by-screen route specs
6. Clicks: what each click opens
7. Actions: what each action executes
8. Backend Contract Alignment
9. QA Journeys
10. Implementation Slices
11. Acceptance Criteria
12. Explicit Non-Goals
```

Each screen section must answer:

```text
- What problem does this screen solve?
- What object is selected or created here?
- What data does the backend load when the route opens?
- What does each click open?
- What does each action execute?
- What errors, blocked states, empty states, and permission states appear?
- What should never be placed on this screen?
```

## 5. Recommended Documentation Queue

Use this queue after the Master Data redesign is reviewed:

1. `GUI_CATALOG_CORE_ROADMAP_SPEC.md`
   Because schema packs, official OTM paths, Data Dictionary references, and
   macro-object search are now shared inputs for Master Data, Rates,
   Integration Mapping, and Order Release Generator.
2. `GUI_SHELL_AUTH_SIGNOUT_RECOVERY_SPEC.md`
   Because the 2026-05-26 browser pass showed the login form can appear while
   authenticated sidebar navigation remains visible after sign out.
3. `GUI_GLOBAL_ACTION_DESTINATION_CONTRACT.md`
   Because Project Cockpit global actions like `View jobs` and `View evidence`
   need route-level outcomes instead of invisible same-screen clicks.
4. `GUI_ROW_ACCESSIBLE_NAME_CONTRACT.md`
   Because object-list rows currently expose oversized row text as button names
   in several modules.

## 6. Maintenance Rule

When a new module-specific roadmap spec is created:

1. add it to this file;
2. add it to `GUI_CONTRACT_INDEX.md`;
3. link it from `GUI_MODULE_EXPERIENCE_ROADMAP.md`;
4. update or create the matching Linear issue;
5. commit the documentation before implementation begins.
