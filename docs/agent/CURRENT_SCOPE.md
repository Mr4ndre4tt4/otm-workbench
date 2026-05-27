# Current Scope

**Status:** active UI phase consolidation baseline
**Date:** 2026-05-27

## Current Program Direction

The project is in a governance and redesign reset before further module
development. The objective is to recover module intent, validate the near-term
UI surface, consolidate the To-Be mockups in Figma from the supplied PDF,
validated specs, and Complete Solution Mockup, then clean and rebuild the
product module by module.

The current product direction is simplified: OTM Workbench groups accelerators
that can be used at any moment of a project. It should not force a full project
control workflow. The shell/cockpit must prioritize context isolation,
accelerator launch, Public View, and useful project information.

## In Scope Now

- Governance structure under `docs/agent/`.
- Module scope recovery and documentation classification.
- Figma wireframe consolidation from the supplied PDF and validated specs.
- FigJam solution diagnostics that visualize the current as-is stack, module
  boundaries, backend/frontend/database relationships, operational flows,
  function status, and cleanup decision paths.
- Current UI phase navigation limited to:
  - Cockpit;
  - Master Data / Data Factory;
  - Rates Studio;
  - Load Plan / Cutover;
  - Integration Mapping Studio;
  - Order Release Generator;
  - Assets Library;
  - Settings.
- Settings owns the current UI setup surface for projects, client/domain,
  environments, profiles, users, roles, grants, and access policies.
- Future cleanup planning for unnecessary frontend routes, modules, and screens.
- To-Be adaptation planning from the current implementation to the validated
  Complete Solution Mockup deep-flow boards.
- Test scenario and synthetic fixture strategy for module delivery.

## Out Of Scope Now

- Source-code cleanup.
- Route removal.
- UI implementation.
- Linear or GitHub delivery updates.
- Deleting or archiving files.
- Top-level UI for Catalog Core, Evidence Hub, separate Admin Console / Jobs,
  Developer Tools, Coordinate Quality, generic dashboards, readiness boards,
  workstream boards, blocker boards, activity timelines, or job dashboards.

## Current UI Phase Module Set

| Module | Current specific source | Current UI phase interpretation |
|---|---|---|
| Shell / Project Cockpit | `docs/otm-workbench/gui/GUI_PROJECT_COCKPIT_CONSOLIDATED_SPEC.md` | Active. Context selector, accelerator launcher, Public View entry, and project info hub. Not a readiness/workstream dashboard. |
| Master Data / Data Factory | `docs/otm-workbench/gui/GUI_MASTER_DATA_DATA_FACTORY_REDESIGN_SPEC.md` | Active. Data Factory, Template Builder, batch validation, and Quality Tools inside the Master Data route family. |
| Rates Studio | `docs/otm-workbench/gui/GUI_RATES_STUDIO_CONSOLIDATED_SPEC.md` | Active. Tariff lifecycle, validation, approval, artifacts, and Load Plan handoff. |
| Load Plan / Cutover | `docs/otm-workbench/gui/GUI_LOAD_PLAN_CUTOVER_CONSOLIDATED_SPEC.md` | Active. Package review, CSVUTIL sequencing, readiness, go/no-go, and cutover handoff. |
| Integration Mapping Studio | `docs/otm-workbench/gui/GUI_INTEGRATION_MAPPING_CONSOLIDATED_SPEC.md` | Active. Mapping definition, schema binding, rules, preview, artifacts, and integration evidence. |
| Order Release Generator | `docs/otm-workbench/gui/GUI_ORDER_RELEASE_GENERATOR_CONSOLIDATED_SPEC.md` | Active. Template-guided order release generation, XML preview/artifacts, and guarded submit readiness. |
| Assets Library | `docs/otm-workbench/gui/GUI_ASSETS_LIBRARY_CONSOLIDATED_SPEC.md` | Active. Controlled asset/version/link library, not a generic file manager. |
| Settings | `docs/otm-workbench/gui/GUI_ADMIN_CONSOLE_CONSOLIDATED_SPEC.md` | Active UI consolidation of project creation, client/domain, environments, profiles, users, roles, grants, and access policies. |
| Catalog Core | `docs/otm-workbench/gui/GUI_CATALOG_CORE_ROADMAP_SPEC.md` | Out of top-level UI for this phase. Remains a backend/internal validation dependency for Data Dictionary, macro objects, schemas, and OTM dependency validation. |
| Evidence Hub | `docs/otm-workbench/gui/GUI_EVIDENCE_HUB_CONSOLIDATED_SPEC.md` | Out of top-level UI for this phase. Evidence and artifacts stay module-local or backend-traceable until reintroduced. |
| Admin Console / Jobs | `docs/otm-workbench/gui/GUI_ADMIN_CONSOLE_CONSOLIDATED_SPEC.md` | Not a separate top-level UI module in this phase. Setup scope is absorbed into Settings; job dashboards stay out. |
| Developer Tools | `docs/otm-workbench/gui/GUI_DEVELOPER_TOOLS_CONSOLIDATED_SPEC.md` | Out of main UI for this phase. Keep technical diagnostics restricted and hidden from normal workflows. |
| Coordinate Quality | `docs/otm-workbench/gui/GUI_MASTER_DATA_DATA_FACTORY_REDESIGN_SPEC.md` | Not a top-level module. It remains Master Data Quality Tools scope. |

## Active To-Be Figma Artifact

```text
OTM Workbench - Complete Solution Mockup
file-key: 7AkORIWrjmaOiBBA6cMOj9
https://www.figma.com/design/7AkORIWrjmaOiBBA6cMOj9/OTM-Workbench---Complete-Solution-Mockup
active page: 00 Analysis + Visual System
```

The active To-Be Figma page now contains seven deep-flow boards:

- `10 / Rates Studio Deep Flow`;
- `11 / Assets Library Deep Flow`;
- `12 / Load Plan Deep Flow`;
- `13 / Order Release Deep Flow`;
- `14 / Integration Mapping Deep Flow`;
- `15 / Configuration Settings Deep Flow`;
- `16 / Cockpit v3 Deep Flow`.

Validation in Figma passed with 112 screen cards, no card overlaps, no text
overflow, consistent spacing, and IBM Plex Sans visual grammar.

Supporting previous Figma file:

```text
OTM Workbench - Consolidated Scope Wireframes
https://www.figma.com/design/zJGLRJCTArRStISGIPQ2DQ
supporting page: Current Scope v2 - Prototype DNA
```

The consolidated wireframe file remains useful as historical/supporting
evidence. The active To-Be visual source is the Complete Solution Mockup.

## Active FigJam Diagnostic Artifact

```text
OTM Workbench - Stack As-Is Map
https://www.figma.com/board/4oR1pKe0Ia3g5IeJlkLnh2
```

The FigJam board contains the current solution diagnostic diagrams:

- stack as-is map;
- UI scope boundary;
- module implementation matrix;
- backend/frontend/database by module;
- operational flow from as-is to target;
- cleanup decision flow;
- function status by module;
- core data model overview.

See:

- `docs/agent/figma-wireframes/OTM_WORKBENCH_AS_IS_SOLUTION_DIAGRAMS_REPORT.md`

## Active Priority

Priority is not more code. Priority is:

1. use the Complete Solution Mockup deep-flow boards as the To-Be UX baseline;
2. classify current frontend routes/components as keep, hide, absorb, alter,
   archive, remove, or create;
3. clean the frontend navigation surface by hiding/removing modules not being
   attacked now, without deleting backend/internal dependencies prematurely;
4. plan and implement client/domain plus environment segregation;
5. finish Settings;
6. finish Cockpit;
7. proceed through Rates, Assets, Master Data, Integration, and Order Release;
8. revalidate each module before delivery against its desired outcome,
   generated artifacts, tests, docs, Linear, GitHub, and QA evidence.

The complete module documentation index is:

- `docs/agent/MODULE_DOCUMENTATION_INDEX.md`
- `docs/agent/TO_BE_SOLUTION_ALIGNMENT_PLAN.md`
- `docs/agent/TEST_SCENARIO_FIXTURE_STRATEGY.md`
