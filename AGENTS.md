# OTM Workbench Agent Map

This file is the short entry point for Codex or any future agent working in
this repository.

## Project Shape

- Product: OTM Workbench, a local-first modular workbench for Oracle
  Transportation Management implementation, data preparation, validation,
  evidence, integrations, and cutover support.
- Architecture: backend-first modular monolith with React/Vite frontend.
- Source of truth: repository docs and code. Linear is the visibility board.
- Current delivery mode: governance reset, module scope recovery, Complete
  Solution Mockup To-Be consolidation from validated specs and the supplied
  PDF, approved frontend cleanup, client/domain and environment segregation,
  then structured module-by-module development.
- Current UI phase modules: Cockpit, Master Data, Rates, Load Plan,
  Integration, Order Release, Assets, and Settings. Keep Catalog Core,
  Evidence Hub, separate Admin Console / Jobs, Developer Tools, Coordinate
  Quality as a top-level module, and generic dashboards out of the main UI for
  now unless the user reintroduces them.

## Mandatory Rules

- Do not use real client data in docs, fixtures, screenshots, tests, or seeds.
- Every operational record must carry explicit `client/domain`, `environment`,
  and visibility/access-policy scope. Public View is a separate shared scope,
  not a shortcut into private client data.
- Prefer backend-owned labels, icons, capabilities, available actions, statuses,
  preferences, templates, and validation rules.
- Treat Project Cockpit as a context selector, accelerator launcher, Public View
  entry, and project-info hub. Do not turn it into a project-management,
  readiness, workstream, blocker, activity, or jobs dashboard.
- Keep client/domain, environment, user, role, grant, and permission setup in
  Settings for the current UI phase. `DBA` can see all data; normal users
  operate only inside allowed scopes.
- Keep operational workflows, authoring workflows, and quality utilities on
  separate route families unless a module spec explicitly says otherwise.
- Complex object details, edit, copy, delete/retire, and result inspection must
  use a route-level screen or a deliberate modal with a visible return path.
- Always validate OTM table dependencies through the Data Dictionary and use
  official Oracle documentation for technical/functional uncertainty.
- For OTM CSVs, first line is table name, second line is columns, then values;
  if dates are present, emit the `exec alter session ...` date format line
  before values.
- Update docs, Linear, GitHub, tests, and QA evidence together when a delivery
  slice changes product behavior.
- Before capturing browser QA evidence, verify that the live backend used by
  the browser exposes the current UI phase navigation. Query
  `/api/v1/platform/navigation` on the same base URL/session, compare the
  returned module IDs with the current scope, and treat any mismatch as stale
  runtime evidence. Restart the backend/dev server or use a fresh port before
  taking screenshots. Screenshots showing excluded top-level modules are
  invalid acceptance evidence.
- At the start of a new chat, treat conversation memory as incomplete until the
  chat-continuity intake gate has been completed. Read
  `docs/agent/CHAT_CONTINUITY_WORKFLOW.md`, latest `HANDOFF.md`, latest
  `VALIDATION_REPORT.md`, `DECISION_LOG.md`, `RISK_REGISTER.md`,
  `CURRENT_SCOPE.md`, and `DELIVERY_PIPELINE.md`, then check
  `git status --short` before acting.
- Before ending a session that changed behavior, docs, tests, QA evidence,
  Linear, GitHub, or design artifacts, leave a handoff capsule in
  `docs/agent/HANDOFF.md` following
  `docs/agent/CHAT_CONTINUITY_WORKFLOW.md`. Do not leave silent partial work.

## Where To Start

1. Read `docs/agent/PROJECT_BRIEF.md`.
2. Read `docs/agent/PROJECT_NORTH_STAR.md`.
3. Read `docs/agent/CURRENT_SCOPE.md`.
4. Read `docs/agent/ROADMAP.md` and `docs/agent/DELIVERY_PIPELINE.md`.
5. Read `docs/otm-workbench/README.md`.
6. Read `docs/otm-workbench/engineering/HARNESS_ENGINEERING_PLAN.md`.
7. Read `docs/otm-workbench/gui/GUI_MODULE_ROADMAP_INDEX.md`.
8. Read `docs/agent/TO_BE_SOLUTION_ALIGNMENT_PLAN.md` and
   `docs/agent/TEST_SCENARIO_FIXTURE_STRATEGY.md`.
9. For current UI/module work, read `docs/agent/MODULE_DOCUMENTATION_INDEX.md`
   and then the matching module scope review, wireframe brief, and source spec.
10. Read `docs/agent/CHAT_CONTINUITY_WORKFLOW.md` and apply the new-chat
   intake gate when this is a new thread or resumed context.
11. Check `git status --short` before editing. Do not revert unrelated user
   changes.

## Governance Controls

- Current north star: `docs/agent/PROJECT_NORTH_STAR.md`.
- Current scope: `docs/agent/CURRENT_SCOPE.md`.
- Module scope recovery: `docs/agent/MODULE_SCOPE_LEDGER.md`.
- Module documentation index: `docs/agent/MODULE_DOCUMENTATION_INDEX.md`.
- Delivery pipeline: `docs/agent/DELIVERY_PIPELINE.md`.
- Chat continuity workflow: `docs/agent/CHAT_CONTINUITY_WORKFLOW.md`.
- Recovery and cleanup planning: `docs/agent/RECOVERY_PLAN.md`.
- Document inventory: `docs/agent/DOCUMENT_INVENTORY.md`.
- Decisions, risks, and handoff:
  `docs/agent/DECISION_LOG.md`, `docs/agent/RISK_REGISTER.md`,
  `docs/agent/HANDOFF.md`.

Do not delete, archive, or mass-move files until the recovery plan identifies
the candidates and the user approves the action.

## Completion Bar

A module is not complete just because it works technically. It is complete only
when it solves the real user problem clearly:

- backend/API contract exists and is tested;
- UI is clear and not overloaded;
- each click has an obvious destination;
- actions execute the expected backend behavior;
- browser QA covers happy, negative, out-of-order, and route recovery paths;
- screenshots/evidence are captured for meaningful states;
- module docs and Linear are current;
- changes are committed and pushed.
