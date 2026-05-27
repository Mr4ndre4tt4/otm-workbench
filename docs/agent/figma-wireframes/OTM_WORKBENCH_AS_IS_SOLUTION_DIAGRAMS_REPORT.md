# OTM Workbench As-Is Solution Diagrams Report

**Status:** active diagnostic artifact
**Date:** 2026-05-27

## Purpose

This report records the FigJam diagnostic board created to make the current
OTM Workbench solution visible before cleanup or further implementation.

The board is not an implementation approval by itself. It is a planning and
analysis artifact that shows where the solution is today, where the current UI
phase wants to go, and which areas need future decisions to keep, hide, absorb,
alter, remove, or create.

## FigJam Artifact

```text
File: OTM Workbench - Stack As-Is Map
File key: 4oR1pKe0Ia3g5IeJlkLnh2
URL: https://www.figma.com/board/4oR1pKe0Ia3g5IeJlkLnh2
Team: otm-workbench
Team ID observed from Chrome/Figma: 1631369663740377053
```

## Source Inputs

- `AGENTS.md`
- `docs/agent/PROJECT_BRIEF.md`
- `docs/agent/PROJECT_NORTH_STAR.md`
- `docs/agent/CURRENT_SCOPE.md`
- `docs/agent/ROADMAP.md`
- `docs/agent/DELIVERY_PIPELINE.md`
- `docs/agent/ARCHITECTURE_MAP.md`
- `docs/agent/MODULE_SCOPE_LEDGER.md`
- `docs/agent/MODULE_DOCUMENTATION_INDEX.md`
- `docs/otm-workbench/README.md`
- `docs/otm-workbench/engineering/HARNESS_ENGINEERING_PLAN.md`
- `docs/otm-workbench/gui/GUI_MODULE_ROADMAP_INDEX.md`
- `pyproject.toml`
- `frontend/package.json`
- backend route files under `src/otm_workbench/`
- frontend route and module files under `frontend/src/`

## Created Diagrams

| Diagram | Purpose |
|---|---|
| `OTM Workbench - Stack As-Is Map` | Shows the current stack, users, frontend, backend, persistence, artifacts, docs, and external visibility systems. |
| `OTM Workbench - UI Scope Boundary` | Separates active UI phase modules from internal, absorbed, or excluded surfaces. |
| `OTM Workbench - Module Implementation Matrix` | Summarizes module status and future decision types: keep, alter, absorb, hide, cut, or create. |
| `OTM Workbench - Backend Frontend DB By Module` | Maps active module views to FastAPI routers, SQLAlchemy model groups, artifacts, manifests, and evidence. |
| `OTM Workbench - Operational Flow As-Is To Target` | Shows the intended user flow from login/context selection to accelerator use, validation, artifact creation, evidence, review, and handoff. |
| `OTM Workbench - Cleanup Decision Flow` | Defines the decision path before hiding, absorbing, archiving, removing, altering, or creating work. |
| `OTM Workbench - Function Status By Module` | Groups implemented/evidenced functionality, current target shape, and to-be-built or reshaped work. |
| `OTM Workbench - Core Data Model Overview` | Gives a high-level ER view of platform, module, artifact, evidence, OTM catalog, and cutover entities. |

## Consolidated As-Is Reading

The current solution is backend-rich. Many module capabilities already exist in
FastAPI routes, SQLAlchemy models, tests, and frontend module views:

- Platform owns authentication, active context, navigation, capabilities,
  jobs, artifacts, manifests, evidence, and audit.
- Catalog Core has Data Dictionary, macro-object, schema, reference, and OTM
  dependency validation capability.
- Master Data has templates, batches, workbook editing, CSV generation,
  direct OTM import guards, and Coordinate Quality under Quality Tools.
- Rates has batches, validation, approval, CSV preview/export, evidence, and
  reference/dictionary surfaces.
- Load Plan has packages, CSVUTIL builds, ZIP analysis, review queue,
  sequencing, readiness, go/no-go, exports, and handoff.
- Integration Mapping has systems, definitions, payload artifacts, schema
  trees, mappings, loops, joins, join bindings, lookups, response handlers,
  previews, generated specs, artifacts, and audit events.
- Order Release Generator has templates, batches, XML preview/artifacts, and
  guarded submit readiness.
- Assets has classifications, asset lifecycle, links, versions, downloads, and
  archive behavior.

The frontend also contains routes for modules that are no longer top-level UI
targets in the current phase, including Catalog Core, Evidence Hub, Admin
Console / Jobs, Developer Tools, and Coordinate Quality evidence through Master
Data.

## Current Target Reading

The current UI phase should keep only these top-level surfaces:

1. Cockpit
2. Master Data / Data Factory
3. Rates Studio
4. Load Plan / Cutover
5. Integration Mapping Studio
6. Order Release Generator
7. Assets Library
8. Settings

Settings absorbs project creation, client/domain, environments, profiles,
users, roles, grants, and access policies for this phase.

Catalog Core remains a backend/internal validation dependency. Evidence Hub
stays module-local or backend-traceable until reintroduced. Developer Tools
remain restricted and out of normal workflows. Admin/Jobs are not separate
top-level UI surfaces for now. Coordinate Quality stays under Master Data
Quality Tools rather than returning as a standalone top-level module.

## Planning Implications

- Do not start source cleanup from route existence alone; first decide whether
  a route is active UI, internal dependency, absorbed setup, or excluded
  top-level surface.
- Keep backend services that provide validation or traceability even when their
  top-level UI route is hidden.
- Treat Cockpit simplification and Settings creation as high-value alignment
  work before broad implementation resumes.
- Approval/export/submit operations need deliberate route-level review screens
  or modals with visible return paths.
- Cleanup requires a reviewed candidate list and explicit user approval before
  archive moves or code removal.

## Validation

Validation performed:

- repository docs and code were inspected;
- the `otm-workbench` Figma team was identified through the open Chrome/Figma
  tab;
- the FigJam board was generated in the `otm-workbench` team;
- all eight diagrams were generated into the same FigJam file.

Validation not performed:

- backend tests;
- frontend tests;
- lint/build;
- browser QA against the local app.

Those checks were not run because this slice created documentation and visual
diagnostic artifacts only.

## Next Step

Review the FigJam diagnostic board with the user and Michelangelo, then create
a cleanup candidate list that classifies each route/component/doc as:

- keep;
- hide from navigation;
- absorb into another module;
- alter route/component shape;
- archive reversibly;
- remove with tests;
- create as missing target work.
