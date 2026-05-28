# Document Inventory

**Status:** initial category-level inventory
**Date:** 2026-05-27

## Inventory Rules

Classifications:

- `active`: current source of truth or control doc;
- `supporting`: useful evidence or reference, but not the main source;
- `superseded`: replaced by a newer doc;
- `duplicate`: overlaps another doc without adding durable value;
- `unknown`: needs review;
- `archive-candidate`: likely safe to archive after approval.

No file is archived by this inventory alone.

## Active Governance Docs

| Path | Classification | Notes |
|---|---|---|
| `AGENTS.md` | active | Short agent entry point. |
| `docs/agent/PROJECT_NORTH_STAR.md` | active | Current north star. |
| `docs/agent/CURRENT_SCOPE.md` | active | Current reorganization scope. |
| `docs/agent/ROADMAP.md` | active | New phased roadmap. |
| `docs/agent/DELIVERY_PIPELINE.md` | active | New delivery process. |
| `docs/agent/CHANGE_CONTROL.md` | active | Direction-change rules. |
| `docs/agent/CHAT_CONTINUITY_WORKFLOW.md` | active | New-chat intake and previous-chat handoff workflow. |
| `docs/agent/DECISION_LOG.md` | active | Durable decisions. |
| `docs/agent/PENPOT_CONNECTOR_DIAGNOSTIC.md` | supporting | Penpot connector diagnosis from the earlier cockpit pass; current visual target is Figma. |
| `docs/agent/RISK_REGISTER.md` | active | Active risks. |
| `docs/agent/HANDOFF.md` | active | Current handoff. |
| `docs/agent/VALIDATION_REPORT.md` | active | Current validation evidence and QA notes. |
| `docs/agent/MODULE_DOCUMENTATION_INDEX.md` | active | Index for all module scope reviews and wireframe briefs. |
| `docs/agent/TASK_CONTRACT_TO_BE_ALIGNMENT.md` | active | Contract for the current documentation consolidation and To-Be planning slice. |
| `docs/agent/TO_BE_SOLUTION_ALIGNMENT_PLAN.md` | active | Current plan for adapting the implementation to the Complete Solution Mockup To-Be state. |
| `docs/agent/TEST_SCENARIO_FIXTURE_STRATEGY.md` | active | Cross-module scenario and valid synthetic fixture strategy. |
| `docs/agent/TASK_CONTRACT_FRONTEND_NAVIGATION_PRUNING.md` | active | Contract for the first frontend cleanup implementation slice. |
| `docs/agent/FRONTEND_NAVIGATION_PRUNING_REPORT.md` | active | Implementation report for pruning main navigation to the To-Be UI phase. |
| `docs/agent/module-scope/*.md` | active | Module-by-module scope validation notes. |
| `docs/agent/wireframe-briefs/*.md` | active | Michelangelo briefs for Figma/current visual wireframing. |
| `docs/agent/penpot-wireframes/*.md` and `docs/agent/penpot-wireframes/*.json` | supporting | Penpot-ready build packets and creation reports from earlier cockpit passes. |
| `docs/agent/figma-wireframes/*.md` | active | Current Figma consolidation reports for the limited UI phase. |
| `docs/agent/figma-wireframes/OTM_WORKBENCH_COMPLETE_SOLUTION_DEEP_FLOW_REPORT.md` | active | Current To-Be Figma deep-flow report for the Complete Solution Mockup. |
| `docs/agent/figma-wireframes/OTM_WORKBENCH_AS_IS_SOLUTION_DIAGRAMS_REPORT.md` | active | Report for the FigJam as-is solution diagnostic board. |

## Superseded Governance Artifacts

| Path | Classification | Notes |
|---|---|---|
| `docs/agent/penpot-wireframes/PROJECT_COCKPIT_WIREFRAME_BLUEPRINT.json` | superseded | Project Cockpit v1 board set over-scoped the Cockpit as a project-control dashboard. Replaced by `PROJECT_COCKPIT_V2_WIREFRAME_BLUEPRINT.json`. |
| `docs/agent/penpot-wireframes/PROJECT_COCKPIT_PENPOT_CREATION_REPORT.md` | supporting/superseded | Useful evidence of v1 Penpot creation and connector behavior. Generated v1 boards were later removed from Penpot. |
| `docs/agent/penpot-wireframes/PROJECT_COCKPIT_V2_WIREFRAME_BLUEPRINT.json` | superseded | Project Cockpit v2.1 evidence. Generated v2.1 boards were later removed from Penpot. Replaced by `PROJECT_COCKPIT_V3_WIREFRAME_BLUEPRINT.json`. |
| `docs/agent/penpot-wireframes/PROJECT_COCKPIT_V2_PENPOT_CREATION_REPORT.md` | supporting/superseded | Penpot v2.1 evidence. Replaced by `PROJECT_COCKPIT_V3_PENPOT_CREATION_REPORT.md`. |
| `docs/agent/penpot-wireframes/PROJECT_COCKPIT_V3_WIREFRAME_BLUEPRINT.json` | active | Current Project Cockpit v3 blueprint. |
| `docs/agent/penpot-wireframes/PROJECT_COCKPIT_V3_PENPOT_CREATION_REPORT.md` | active | Current Project Cockpit v3 Penpot creation and cleanup evidence. |
| `docs/agent/figma-wireframes/OTM_WORKBENCH_UI_PHASE_CONSOLIDATION_REPORT.md` | supporting | Previous active Figma consolidation. Superseded as active visual target by the Complete Solution Mockup, but still useful as supporting evidence. |
| `docs/agent/figma-wireframes/OTM_WORKBENCH_WIREFRAME_AUDIT_REPORT_2026_05_27.md` | supporting | Previous audit gap report; many route-depth gaps were addressed by the Complete Solution Mockup deep-flow boards. |

## Active Product And Engineering Docs

| Path | Classification | Notes |
|---|---|---|
| `docs/otm-workbench/README.md` | active | Deep documentation entry point. |
| `docs/otm-workbench/engineering/HARNESS_ENGINEERING_PLAN.md` | active | Harness operating model. |
| `docs/otm-workbench/governance/GITHUB_DELIVERY_GOVERNANCE.md` | active | Active GitHub Issues/PRs/Actions delivery governance. |
| `docs/otm-workbench/governance/GITHUB_VERSIONING_AND_ISSUE_CADENCE.md` | active | Lightweight GitHub version-train, issue cadence, and commit granularity workflow. |
| `docs/otm-workbench/governance/CODERABBIT_REVIEW_GOVERNANCE.md` | active | Assistive CodeRabbit review policy. |
| `docs/otm-workbench/governance/LINEAR_DELIVERY_GOVERNANCE_OTM62.md` | supporting | Historical Linear governance. Linear is paused unless explicitly reactivated. |
| `docs/otm-workbench/gui/GUI_MODULE_ROADMAP_INDEX.md` | active | GUI module index. |
| `docs/otm-workbench/gui/GUI_MODULE_COMPLETION_ACCEPTANCE_CONTRACT.md` | active | Module completion bar. |
| `docs/otm-workbench/gui/GUI_CONTRACT_INDEX.md` | active | GUI contract index. |

## Active Module Specs

| Module | Path | Classification |
|---|---|---|
| Project Cockpit | `docs/otm-workbench/gui/GUI_PROJECT_COCKPIT_CONSOLIDATED_SPEC.md` | active |
| Master Data / Data Factory | `docs/otm-workbench/gui/GUI_MASTER_DATA_DATA_FACTORY_REDESIGN_SPEC.md` | active |
| Catalog Core | `docs/otm-workbench/gui/GUI_CATALOG_CORE_ROADMAP_SPEC.md` | active |
| Rates Studio | `docs/otm-workbench/gui/GUI_RATES_STUDIO_CONSOLIDATED_SPEC.md` | active |
| Load Plan / Cutover | `docs/otm-workbench/gui/GUI_LOAD_PLAN_CUTOVER_CONSOLIDATED_SPEC.md` | active |
| Evidence Hub | `docs/otm-workbench/gui/GUI_EVIDENCE_HUB_CONSOLIDATED_SPEC.md` | active |
| Assets Library | `docs/otm-workbench/gui/GUI_ASSETS_LIBRARY_CONSOLIDATED_SPEC.md` | active |
| Integration Mapping Studio | `docs/otm-workbench/gui/GUI_INTEGRATION_MAPPING_CONSOLIDATED_SPEC.md` | active |
| Order Release Generator | `docs/otm-workbench/gui/GUI_ORDER_RELEASE_GENERATOR_CONSOLIDATED_SPEC.md` | active |
| Admin Console / Jobs | `docs/otm-workbench/gui/GUI_ADMIN_CONSOLE_CONSOLIDATED_SPEC.md` | active |
| Developer Tools | `docs/otm-workbench/gui/GUI_DEVELOPER_TOOLS_CONSOLIDATED_SPEC.md` | active |

Current UI phase note:

- Top-level UI now includes only Cockpit, Master Data, Rates, Load Plan,
  Integration, Order Release, Assets, and Settings.
- Catalog Core, Evidence Hub, separate Admin Console / Jobs, Developer Tools,
  and Coordinate Quality remain documented, but are not top-level UI modules
  for this phase.
- Settings is the active UI setup surface for projects, client/domain,
  environments, profiles, users, roles, grants, and access policies.
- Active To-Be UX source is the Complete Solution Mockup deep-flow board set.

## Supporting Historical And Evidence Docs

| Path or group | Classification | Notes |
|---|---|---|
| `docs/otm-workbench/gui/*_VIEW.md` | supporting | Older module view contracts; useful as historical evidence until each replacement is confirmed. |
| `docs/otm-workbench/gui/*COMPLETION_REVIEW*.md` | supporting | Evidence and acceptance records. |
| `docs/otm-workbench/gui/*VISUAL_QA*.md` | supporting | Visual QA evidence. |
| `docs/otm-workbench/gui/*PATTERN_CONTRACT.md` | active/supporting | Active where referenced by current UI contract index; review individually before archive. |
| `docs/superpowers/specs/*.md` | supporting | Original design specs and historical decisions. |
| `docs/superpowers/plans/*.md` | supporting | Implementation plans and traceability records. |
| `docs/otm-workbench/foundation/*.md` | active/supporting | Foundational product and architecture source. |

## Active To-Be Implementation Plans

| Path | Classification | Notes |
|---|---|---|
| `docs/agent/TASK_CONTRACT_CONTEXT_SEGREGATION_FOUNDATION.md` | active | Contract for planning client/domain, environment, Public View, and access-policy segregation before schema changes. |
| `docs/agent/CONTEXT_SEGREGATION_MODEL_LEDGER.md` | active | Classification ledger for model families before scope migrations. |
| `docs/superpowers/plans/2026-05-27-context-segregation-foundation.md` | active | Staged implementation plan for backend scoping utility, behavior-lock tests, shared artifact/assets retrofit, Settings authority, module retrofit order, and fixture strategy. |

## Unknown Or Needs Review

| Path or group | Classification | Review reason |
|---|---|---|
| `docs/otm-workbench/gui/GUI_*_EXTRACTION.md` | unknown | May be useful design-system extraction evidence or may be superseded by pattern contracts. |
| `docs/otm-workbench/gui/GUI_BROWSER_QA_ATTEMPT.md` | unknown | Needs comparison with newer QA evidence. |
| `docs/otm-workbench/gui/GUI_GALLERY_VISUAL_QA_ATTEMPT.md` | unknown | Needs comparison with current component gallery evidence. |
| `docs/otm-workbench/roadmap/backlog_pos_rates.md` | unknown | Needs reconciliation with new roadmap. |
| Older Figma consolidation reports that still use pre-To-Be wording for `zJGLRJCTArRStISGIPQ2DQ` | unknown | Needs wording review now that the Complete Solution Mockup is the current To-Be source. |

## Initial Archive Candidates For Later Approval

No files are approved for archive yet.

Candidate groups for detailed review:

- old `*_VIEW.md` docs after consolidated specs fully replace them;
- old QA attempt docs when newer QA pass docs supersede them;
- old extraction notes when token/pattern contracts fully replace them;
- roadmap fragments that conflict with `docs/agent/ROADMAP.md`.
