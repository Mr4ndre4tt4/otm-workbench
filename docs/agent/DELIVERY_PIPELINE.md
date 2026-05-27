# Delivery Pipeline

**Status:** active
**Date:** 2026-05-27

## Pipeline Summary

```text
intake
  -> chat continuity intake when thread changed or memory was compacted
  -> scope recovery
  -> validated active UI phase scope
  -> Michelangelo wireframe brief
  -> FigJam as-is solution diagnostics
  -> Complete Solution Mockup deep-flow boards
  -> To-Be alignment plan
  -> cleanup and context-isolation plan
  -> implementation plan
  -> development slice
  -> tests and browser QA
  -> docs, evidence, GitHub issue/PR/Actions checkpoint
```

## Stage 1: Intake

Inputs:

- repository structure;
- `AGENTS.md`;
- `docs/agent/CHAT_CONTINUITY_WORKFLOW.md` when starting a new chat or resumed
  context;
- docs indexes;
- git status;
- current branch;
- active module specs.

Output:

- current project map;
- recovered current state from durable docs;
- protected files;
- known risks.

New-chat intake rule:

When a new chat starts, context from the previous conversation is treated as
untrusted until reconstructed. The agent must read the latest handoff,
validation report, decision log, risk register, current scope, and delivery
pipeline; run `git status --short`; inspect relevant diffs before editing; and
state the recovered current state before implementation.

## Stage 2: Scope Recovery

Inputs:

- foundation docs;
- consolidated GUI specs;
- Superpowers specs and plans;
- completion reviews;
- browser QA evidence.

Output:

- validated module scope ledger;
- current UI phase module list;
- cleanup watchlist;
- open decisions.

## Stage 3: Wireframe Brief

Owner:

- Michelangelo UX review workflow.

Output:

- task context;
- user profile;
- screen archetypes;
- route map;
- states;
- findings and UX risks;
- acceptance criteria.

Current active UI phase:

- Cockpit
- Master Data / Data Factory
- Rates Studio
- Load Plan / Cutover
- Integration Mapping Studio
- Order Release Generator
- Assets Library
- Settings

Full module brief index:

- `docs/agent/MODULE_DOCUMENTATION_INDEX.md`

## Stage 4: Figma Wireframes And To-Be Mockup

Output:

- low-fidelity wireframes for each active UI phase route;
- consolidated scope map;
- state frames or state notes for blocked, guarded, validation, and
  permission-gated flows;
- review-ready mockups after validation.
- Complete Solution Mockup deep-flow boards for the To-Be route/state model.

Rule:

Wireframes must be derived from the validated module spec, current UI phase
scope, and the supplied PDF, not from adapting the current implementation.

Additional Cockpit rule:

The Cockpit must not become a project-management dashboard. It should expose
client/domain, environment, and Public View context; launch accelerators; and
link to project information. Project lifecycle control, readiness dashboards,
workstreams, blockers, and job dashboards are out of Cockpit scope unless the
user explicitly reintroduces them.

Additional Settings rule:

Settings is the current UI home for project creation, client/domain,
environment, profile, user, role, grant, and access-policy setup. It replaces a
separate Admin Console / Jobs top-level UI for this phase; jobs and developer
diagnostics remain out of the main UI.

## Stage 4A: FigJam As-Is Solution Diagnostics

Output:

- stack as-is map;
- active UI vs excluded/internal boundary map;
- module implementation matrix;
- backend/frontend/database by module;
- operational flow from context selection to validation, artifacts, evidence,
  review, and handoff;
- cleanup decision flow;
- function status by module;
- core data model overview.

Artifact:

```text
OTM Workbench - Stack As-Is Map
https://www.figma.com/board/4oR1pKe0Ia3g5IeJlkLnh2
```

Rule:

The diagnostics clarify current state and cleanup planning. They do not approve
route removal, archive moves, source cleanup, or module reintroduction by
themselves.

## Stage 5: Cleanup

Inputs:

- validated mockups;
- `docs/agent/TO_BE_SOLUTION_ALIGNMENT_PLAN.md`;
- `docs/agent/TEST_SCENARIO_FIXTURE_STRATEGY.md`;
- FigJam as-is solution diagnostics;
- route/component inventory;
- module scope ledger;
- recovery plan.

Output:

- approved cleanup plan;
- reversible archive actions for docs;
- code-removal or route-hiding plan with tests.

First cleanup priority:

- remove or hide frontend exposure for modules not being attacked now;
- preserve backend/internal dependencies needed by active modules;
- classify tests and browser scripts before deleting or rewriting them.

## Stage 5A: Context Isolation Foundation

Inputs:

- Settings scope;
- active Cockpit context selector;
- existing backend models and API contracts;
- Data Dictionary and Oracle documentation where OTM table behavior matters.

Output:

- explicit client/domain and environment persistence plan;
- access-policy and Public View behavior;
- `DBA` visibility behavior;
- scoped synthetic fixture plan;
- cross-client and cross-environment test cases.

## Stage 6: Development

Required per slice:

- task contract;
- implementation plan;
- backend tests;
- frontend tests;
- browser QA;
- screenshots/evidence;
- valid synthetic fixtures when files or generated artifacts are part of the
  module;
- Data Dictionary and Oracle documentation notes when OTM behavior is uncertain;
- docs update;
- GitHub Issue/PR update when a slice changes delivery state;
- decision/risk/handoff update when direction changes.
- if the slice may continue in another chat, a handoff capsule following
  `docs/agent/CHAT_CONTINUITY_WORKFLOW.md`.

Runtime freshness gate:

Before any browser QA screenshot or visual acceptance claim, verify the same
live backend/frontend pair used by the browser. The gate is:

1. confirm expected top-level modules from `docs/agent/CURRENT_SCOPE.md`;
2. run or inspect the source-level navigation guard, currently
   `pytest tests/test_modules_navigation.py -q`;
3. query `/api/v1/platform/navigation` on the browser QA backend with the same
   user/session context;
4. compare returned module IDs with the current UI phase and role permissions;
5. if excluded modules appear, or expected allowed modules are missing for the
   test role, stop and restart the backend/dev server or move QA to a fresh
   port;
6. capture screenshots only after the live sidebar and API result match.

Evidence records must name the backend URL, frontend URL, user context, and
the navigation result or the command used to verify it. A screenshot from a
stale runtime is not valid evidence, even when source tests pass.

GitHub delivery gate:

GitHub is the active delivery visibility layer. For each reviewable slice:

1. create or update a GitHub Issue using the delivery or governance template;
2. link the issue from the branch, PR body, or PR comments;
3. let GitHub Actions run backend tests, frontend tests, and frontend build;
4. for broad, risky, security-sensitive, CI, or governance changes, request or
   run CodeRabbit review and triage only actionable findings;
5. record validation commands, evidence, and review status in the PR;
6. keep Linear paused/historical unless the user explicitly reactivates it.

## Stage 7: Completion Review

A module is not complete until the review records:

- scope;
- supported user stories;
- backend contracts;
- generated artifact parity;
- authoring/config coverage;
- positive QA;
- negative QA;
- out-of-order behavior;
- security/client-data safety;
- known gaps.

Each module must be revalidated before implementation starts and again before
completion. Revalidation checks the To-Be Figma board, module scope review,
wireframe brief, GUI spec, desired user outcome, fixture needs, and generated
artifact parity.

## Stop Conditions

Stop and request a decision when:

- scope conflicts with the north star;
- cleanup would delete or archive source code;
- a module lacks validated scope;
- a wireframe contradicts backend-owned truth;
- a route removal would break documented QA evidence;
- an excluded UI module needs to be reintroduced;
- Oracle/OTM behavior is uncertain and not validated.
- live browser QA navigation contradicts the current UI phase scope.
