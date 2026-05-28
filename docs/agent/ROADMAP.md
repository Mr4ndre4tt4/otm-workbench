# Reorganization Roadmap

**Status:** active planning baseline
**Date:** 2026-05-27

## Phase 0: Intake And Freeze

Goal: understand the current repository state before reorganizing.

Outputs:

- `PROJECT_BRIEF.md`
- `ARCHITECTURE_MAP.md`
- `CURRENT_SCOPE.md`
- initial `DOCUMENT_INVENTORY.md`
- protected-area list

Rules:

- no source code changes;
- no file deletion;
- no archive moves;
- identify existing user changes before editing.

## Phase 1: Governance Baseline

Goal: create the Solon control layer.

Outputs:

- `PROJECT_NORTH_STAR.md`
- `ROADMAP.md`
- `DELIVERY_PIPELINE.md`
- `CHANGE_CONTROL.md`
- `DECISION_LOG.md`
- `RISK_REGISTER.md`
- `HANDOFF.md`

## Phase 2: Module Scope Recovery

Goal: recover original scope and validate future target scope per module.

Outputs:

- `MODULE_SCOPE_LEDGER.md`
- module-by-module scope review notes;
- accepted scope decisions in `DECISION_LOG.md`;
- risks and dependencies in `RISK_REGISTER.md`.

Recovery documentation exists for the broader module set, but the current UI
phase only carries forward these top-level surfaces:

1. Cockpit
2. Master Data / Data Factory
3. Rates Studio
4. Load Plan / Cutover
5. Integration Mapping Studio
6. Order Release Generator
7. Assets Library
8. Settings

Catalog Core, Evidence Hub, separate Admin Console / Jobs, Developer Tools, and
Coordinate Quality are not top-level UI modules for this phase.

## Phase 3: Michelangelo Wireframe Briefs

Goal: create UX briefs from validated specs before drawing.

For each active UI phase module:

- user task;
- screen/flow archetype;
- routes;
- primary object;
- primary action;
- states;
- blocked/error/recovery paths;
- accessibility and information architecture risks;
- acceptance criteria.

## Phase 4: Figma Wireframes And Mockups

Goal: create Figma wireframes from validated scope and the supplied PDF, not
from the current UI.

Active To-Be Figma file:

```text
OTM Workbench - Complete Solution Mockup
https://www.figma.com/design/7AkORIWrjmaOiBBA6cMOj9/OTM-Workbench---Complete-Solution-Mockup
active page: 00 Analysis + Visual System
```

Outputs:

- consolidated scope map;
- one route wireframe board per active UI phase module;
- state notes for blocked, guarded, empty, validation, and permission paths;
- review notes;
- validated mockups.
- deep-flow boards for Rates, Assets, Load Plan, Order Release, Integration,
  Configuration/Settings, and Cockpit v3.

Supporting previous Figma file:

```text
OTM Workbench - Consolidated Scope Wireframes
https://www.figma.com/design/zJGLRJCTArRStISGIPQ2DQ
supporting page: Current Scope v2 - Prototype DNA
```

Additional diagnostic artifact:

```text
OTM Workbench - Stack As-Is Map
https://www.figma.com/board/4oR1pKe0Ia3g5IeJlkLnh2
```

This FigJam board provides the as-is solution map before cleanup. It contains
stack, UI boundary, module implementation, backend/frontend/database,
operational flow, cleanup decision, function status, and core data model
diagrams.

Current correction:

```text
The active To-Be design target is now `OTM Workbench - Complete Solution
Mockup`. The previous `Consolidated Scope Wireframes` file remains supporting
evidence. The active UI phase still keeps only Cockpit, Master Data, Rates,
Load Plan, Integration, Order Release, Assets, and Settings in the main UI.
Settings absorbs project, profile, user, role, grant, environment, and access
setup. Catalog Core, Evidence Hub, separate Admin/Jobs, Developer Tools,
Coordinate Quality as top-level, and generic dashboards stay out of the main UI
for now unless explicitly reintroduced.
```

## Phase 5: To-Be Alignment Plan

Goal: align the current solution to the validated To-Be mockup before
implementation resumes.

Inputs:

- Complete Solution Mockup deep-flow boards;
- FigJam as-is solution diagnostics;
- module scope ledger;
- module wireframe briefs;
- current frontend/backend inventory.

Outputs:

- `docs/agent/TO_BE_SOLUTION_ALIGNMENT_PLAN.md`;
- `docs/agent/TEST_SCENARIO_FIXTURE_STRATEGY.md`;
- delivery order;
- module revalidation gate;
- cleanup and context-isolation implementation prerequisites.

## Phase 6: Cleanup Plan

Goal: step back and remove unnecessary work before rebuilding.

Inputs:

- active Figma wireframes;
- FigJam as-is solution diagnostics;
- route/component inventory;
- module scope ledger;
- recovery plan.

Rules:

- inventory first;
- classify each candidate as keep, hide, absorb, alter, archive, remove, or
  create;
- classify routes, components, tests, and docs;
- approve cleanup list;
- archive docs reversibly;
- remove code only with explicit implementation plan and tests.

## Phase 7: Structured Module Development

Goal: rebuild module by module using validated scope and mockups.

Each module requires:

- backend/API contract;
- frontend route plan;
- tests before implementation where practical;
- happy, negative, out-of-order, and route-recovery QA;
- runtime freshness verification proving the browser is using a current
  backend/frontend pair before screenshots are accepted;
- screenshots/evidence;
- docs update;
- GitHub Issue/PR update and Actions validation.
- CodeRabbit review when the slice is broad, risky, governance-heavy, or
  security-sensitive.

Current development order:

1. frontend cleanup and current-phase navigation pruning;
2. client/domain and environment segregation;
3. Settings;
4. Cockpit;
5. Rates Studio;
6. Assets Library;
7. Master Data / Data Factory;
8. Integration Mapping Studio;
9. Order Release Generator.

Load Plan remains in the active UI phase and must be preserved as a package and
handoff dependency; focused implementation order can be reprioritized by user
decision.

## Phase 8: Governance Hardening

Goal: make the process durable.

Candidate improvements:

- GitHub version trains with smaller issue-linked commits;
- automated docs inventory checks;
- route inventory checks;
- screenshot/evidence manifest per module;
- active/superseded doc validation;
- module acceptance dashboard.
