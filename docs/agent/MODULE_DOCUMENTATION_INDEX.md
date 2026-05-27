# Module Documentation Index

**Status:** active
**Date:** 2026-05-27

## Purpose

This index tracks the scope review and Michelangelo wireframe brief for every
documented module, and marks which modules are active in the current Figma UI
phase.

## Current Figma UI Phase

Top-level UI modules:

1. Shell / Login / Logout / Project Cockpit
2. Master Data / Data Factory
3. Rates Studio
4. Load Plan / Cutover
5. Integration Mapping Studio
6. Order Release Generator
7. Assets Library
8. Settings

Out of the top-level UI for this phase:

- Catalog Core;
- Evidence Hub;
- separate Admin Console / Jobs;
- Developer Tools;
- Coordinate Quality as a standalone module.

## Module Documentation Matrix

| Module | Scope review | Wireframe brief | Current UI phase status |
|---|---|---|---|
| Shell / Login / Logout / Project Cockpit | `module-scope/PROJECT_COCKPIT_SCOPE_REVIEW.md` | `wireframe-briefs/PROJECT_COCKPIT_WIREFRAME_BRIEF.md` | Active in Figma consolidation |
| Master Data / Data Factory | `module-scope/MASTER_DATA_DATA_FACTORY_SCOPE_REVIEW.md` | `wireframe-briefs/MASTER_DATA_DATA_FACTORY_WIREFRAME_BRIEF.md` | Active in Figma consolidation |
| Catalog Core | `module-scope/CATALOG_CORE_SCOPE_REVIEW.md` | `wireframe-briefs/CATALOG_CORE_WIREFRAME_BRIEF.md` | Out of top-level UI; remains internal Data Dictionary/dependency source |
| Rates Studio | `module-scope/RATES_STUDIO_SCOPE_REVIEW.md` | `wireframe-briefs/RATES_STUDIO_WIREFRAME_BRIEF.md` | Active in Figma consolidation |
| Load Plan / Cutover | `module-scope/LOAD_PLAN_CUTOVER_SCOPE_REVIEW.md` | `wireframe-briefs/LOAD_PLAN_CUTOVER_WIREFRAME_BRIEF.md` | Active in Figma consolidation |
| Evidence Hub | `module-scope/EVIDENCE_HUB_SCOPE_REVIEW.md` | `wireframe-briefs/EVIDENCE_HUB_WIREFRAME_BRIEF.md` | Out of top-level UI; evidence remains module-local/backend-traceable for now |
| Assets Library | `module-scope/ASSETS_LIBRARY_SCOPE_REVIEW.md` | `wireframe-briefs/ASSETS_LIBRARY_WIREFRAME_BRIEF.md` | Active in Figma consolidation |
| Integration Mapping Studio | `module-scope/INTEGRATION_MAPPING_STUDIO_SCOPE_REVIEW.md` | `wireframe-briefs/INTEGRATION_MAPPING_STUDIO_WIREFRAME_BRIEF.md` | Active in Figma consolidation |
| Order Release Generator | `module-scope/ORDER_RELEASE_GENERATOR_SCOPE_REVIEW.md` | `wireframe-briefs/ORDER_RELEASE_GENERATOR_WIREFRAME_BRIEF.md` | Active in Figma consolidation |
| Admin Console / Jobs | `module-scope/ADMIN_CONSOLE_JOBS_SCOPE_REVIEW.md` | `wireframe-briefs/ADMIN_CONSOLE_JOBS_WIREFRAME_BRIEF.md` | Absorbed into Settings for setup; separate Jobs UI out of scope |
| Developer Tools | `module-scope/DEVELOPER_TOOLS_SCOPE_REVIEW.md` | `wireframe-briefs/DEVELOPER_TOOLS_WIREFRAME_BRIEF.md` | Out of main UI |
| Coordinate Quality | `module-scope/COORDINATE_QUALITY_SCOPE_REVIEW.md` | `wireframe-briefs/COORDINATE_QUALITY_WIREFRAME_BRIEF.md` | Master Data Quality Tools scope, not top-level navigation |

## Gate Before Figma Review

Figma review should check:

- the limited active UI phase list;
- the module's scope review;
- the module's wireframe brief;
- the rule that wireframes use validated scope and the supplied PDF, not the
  current UI.

## Active Figma Artifact

```text
OTM Workbench - Complete Solution Mockup
https://www.figma.com/design/7AkORIWrjmaOiBBA6cMOj9/OTM-Workbench---Complete-Solution-Mockup
active page: 00 Analysis + Visual System
```

See:

- `docs/agent/figma-wireframes/OTM_WORKBENCH_COMPLETE_SOLUTION_DEEP_FLOW_REPORT.md`
- `docs/agent/figma-wireframes/OTM_WORKBENCH_UI_PHASE_CONSOLIDATION_REPORT.md`

The previous `OTM Workbench - Consolidated Scope Wireframes` file remains
supporting evidence. The active To-Be UX reference is the Complete Solution
Mockup deep-flow board set.

## Current Implementation Order

1. Frontend cleanup and current-phase navigation pruning.
2. Client/domain and environment segregation foundation.
3. Settings.
4. Cockpit.
5. Rates Studio.
6. Assets Library.
7. Master Data / Data Factory.
8. Integration Mapping Studio.
9. Order Release Generator.

Load Plan remains in the active UI phase and must be preserved as a dependency
for package, CSVUTIL, handoff, and cutover behavior.

## Penpot-Ready Build Packets

| Module | Build spec | Blueprint | Status |
|---|---|---|---|
| Shell / Login / Logout / Project Cockpit v1 | `penpot-wireframes/PROJECT_COCKPIT_PENPOT_BUILD_SPEC.md` | `penpot-wireframes/PROJECT_COCKPIT_WIREFRAME_BLUEPRINT.json` | Superseded reference; created in Penpot but over-scoped |
| Shell / Login / Logout / Project Cockpit v2.1 | `module-scope/PROJECT_COCKPIT_SCOPE_REVIEW.md` | `penpot-wireframes/PROJECT_COCKPIT_V2_WIREFRAME_BLUEPRINT.json` | Superseded by v3; generated boards removed from Penpot |
| Shell / Login / Logout / Project Cockpit v3 | `module-scope/PROJECT_COCKPIT_SCOPE_REVIEW.md` | `penpot-wireframes/PROJECT_COCKPIT_V3_WIREFRAME_BLUEPRINT.json` | Supporting Penpot reference; current visual consolidation moved to Figma |

## Gate Before Cleanup

Cleanup should start only after:

- the Complete Solution Mockup deep-flow boards are validated;
- cleanup candidates are listed;
- the user approves archive or code-removal actions;
- source cleanup has a separate implementation plan and tests.

## Gate Before Module Development

Before each module delivery, revalidate:

- desired user outcome;
- primary object lifecycle;
- active Figma board;
- module scope review;
- wireframe brief;
- GUI source spec;
- backend/API contracts;
- required synthetic fixture files;
- Data Dictionary and Oracle documentation dependencies;
- happy, negative, out-of-order, permission, context-isolation, and
  route-recovery scenarios.
