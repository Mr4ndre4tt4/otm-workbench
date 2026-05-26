# Harness Engineering Plan

**Status:** active operating model  
**Date:** 2026-05-26  
**Scope:** how OTM Workbench should apply harness engineering practices to keep
Codex, future agents, tests, UI QA, Linear, GitHub, and documentation working
as one system.

## 1. Purpose

This plan adapts OpenAI's Harness Engineering guidance to OTM Workbench. The
goal is not to add another project-management layer. The goal is to make the
repository easy for agents and humans to operate safely:

- a new agent should quickly know what the project is, where the contracts are,
  and what must not be broken;
- every module should expose testable backend, frontend, route, and QA
  contracts;
- evidence should be saved in predictable places;
- Linear should show the delivery state without becoming the source of truth;
- GitHub should preserve every meaningful delivery step.

Reference: [OpenAI Harness Engineering](https://openai.com/index/harness-engineering/).

## 2. Project Rule

The repository is the source of truth. Linear is the visibility board. Browser
screenshots and test outputs are evidence. Chat is discussion.

That means every important decision should land in one of these places:

| Decision type | System of record |
|---|---|
| Module objective and UX flow | `docs/otm-workbench/gui/*_CONSOLIDATED_SPEC.md` or module redesign spec |
| Engineering standard | `docs/otm-workbench/engineering/` or `docs/otm-workbench/foundation/` |
| Agent orientation | `AGENTS.md` |
| Delivery task | Linear issue |
| Implemented change | Git commit on `main` or feature branch |
| QA evidence | tests, browser scripts, screenshots under ignored `output/`, and linked docs |

## 3. Agent Entry Points

Every future agent should start with the shortest useful map, then drill down:

1. `AGENTS.md`
2. `docs/otm-workbench/README.md`
3. `docs/otm-workbench/gui/GUI_MODULE_ROADMAP_INDEX.md`
4. the active module spec, starting with
   `docs/otm-workbench/gui/GUI_MASTER_DATA_DATA_FACTORY_REDESIGN_SPEC.md`
5. the matching backend/API tests and browser QA scripts

The root `AGENTS.md` must stay short. It should not duplicate full specs. It
should point to the right contracts and list hard rules that apply to every
change.

## 4. Harness Standards For Every Module

Each module must have a repeatable harness before it can be called complete.

### 4.1 Product Harness

Each module spec must answer:

- what real problem the module solves;
- what each route/screen is responsible for;
- what each click opens;
- what each action executes in the backend;
- what data the backend owns;
- what is explicitly out of scope.

### 4.2 Backend Harness

Backend completion requires:

- typed request/response models;
- service tests for happy path and negative path;
- persistence tests where state changes;
- artifact/evidence tests where files are produced;
- no real client data in fixtures.

### 4.3 Frontend Harness

Frontend completion requires:

- route-level screens for complex object details, edit, copy, delete/retire,
  and result inspection;
- visible `Back` action on drill-down routes;
- no overloaded one-page workflows;
- backend-owned labels, icons, status, available actions, disabled reasons,
  permissions, and preferences wherever practical;
- consistent light/dark-mode behavior through shared tokens.

### 4.4 Browser QA Harness

Every module needs browser scripts that attempt to behave like a real human:

- happy path;
- negative path;
- out-of-order path;
- leave route and return;
- select another object mid-flow;
- try actions when the state is not ready;
- capture screenshots for the meaningful states.

The question at the end of QA is:

```text
Does this solve the real user problem clearly, without making the user guess?
```

If the answer is no, the module is not complete even if tests pass.

## 5. UI And UX Invariants

These invariants are mandatory until a module spec explicitly grants an
exception:

1. One primary job per screen.
2. Complex selected objects open a route-level detail screen, not a crowded side
   panel.
3. Create/edit/copy/delete flows open dedicated routes or modals with a clear
   return path.
4. Operational flow and authoring flow stay separate.
5. Quality utilities stay separate unless they are truly part of the operational
   execution path.
6. Buttons, icons, labels, and action availability should come from backend
   contracts or backend-owned registries.
7. The UI must not depend on hidden action buttons below long scroll regions.
8. Status chips must describe lifecycle or readiness, not project planning terms
   such as `planned` when that does not help the operator.

## 6. Linear And GitHub Loop

Linear issues should be small enough to match a delivery slice. For each slice:

1. create or update the Linear issue before implementation;
2. keep the issue title outcome-based;
3. link or name the module spec section;
4. commit implementation and docs together when they are inseparable;
5. push to GitHub after validation;
6. close or update Linear with QA evidence and remaining risk.

Linear must not replace docs. If an issue contains durable product decisions,
move them to docs and keep the Linear issue as delivery tracking.

## 7. Documentation Garbage Collection

Harness engineering only works if context stays navigable. During each module
cycle:

- mark superseded docs instead of letting conflicting docs remain active;
- keep module index rows current;
- remove or demote stale "MVP complete" claims when the current UI no longer
  meets the acceptance bar;
- prefer one consolidated spec per module plus supporting evidence docs;
- keep screenshots in ignored `output/` and reference them from docs when they
  matter.

## 8. Implementation Plan

### Phase 1: Agent Orientation Baseline

- Add root `AGENTS.md`.
- Link this plan from the docs README and foundation index.
- Add a roadmap note that every module redesign must satisfy the harness
  standard.

### Phase 2: Master Data Harness Completion

- Continue Data Factory redesign Slice 2B with route-level batch detail.
- Add browser QA that starts from the hub and validates template detail, batch
  detail, return behavior, and invalid/out-of-order actions.
- Record screenshots and update the Master Data spec implementation log.

### Phase 3: Module-By-Module Harness

Apply the same pattern in order:

1. Rates Studio
2. Load Plan / Cutover
3. Assets Library
4. Integration Mapping Studio
5. Order Release Generator
6. Evidence Hub
7. Project Cockpit
8. Admin Console
9. Developer Tools

Each module only advances when backend, frontend, browser QA, docs, Linear, and
GitHub are aligned.

### Phase 4: Harness Hardening

- Add shared screenshot naming conventions.
- Add a QA manifest per module.
- Add route inventory checks.
- Add UI invariant checks where they can be automated.
- Add docs consistency checks for active/superseded module specs.

## 9. Acceptance Criteria

This harness plan is working when:

- a new agent can understand the active task in under five minutes from
  `AGENTS.md`;
- each module has one active UX/product spec;
- Linear mirrors the real delivery state;
- commits include docs/test evidence for meaningful product changes;
- browser QA catches confusing workflows before the user does;
- no module is marked complete only because APIs and tests pass.
