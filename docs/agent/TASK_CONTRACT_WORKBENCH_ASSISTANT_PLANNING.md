# Task Contract: Workbench Assistant Planning

## Objective

Plan the long-term design for a lightweight, local-first Workbench Assistant
embedded in OTM Workbench without changing the active module roadmap or current
implementation sequence.

## Original User Request

The user wants to plan a focused assistant for consultants inside OTM Workbench.
The assistant should be opened from a small truck-driver robot icon in the lower
right corner, stay lightweight enough to run locally on common consultant
machines, and help with Workbench usage, templates/files, OTM Data Dictionary
SQL assistance, saved queries, and official Oracle documentation lookup.

The user explicitly asked for extensive design documentation, stack planning,
diagrams, macroflows, microflows, and installation/software planning before any
implementation.

## Interpreted Scope

This is a separate planning track. It defines the target architecture and
design direction for a future cross-cutting assistant layer. It does not add a
new top-level UI module, and it does not interrupt the current Assets/module
delivery sequence.

## In Scope

- Target product definition for the Workbench Assistant.
- Architecture and stack options compatible with the existing repository.
- Macroflow and microflow documentation.
- Mermaid diagrams for architecture, request routing, indexing, SQL helper, and
  Oracle documentation lookup.
- Local-first runtime constraints and cost controls.
- Software and dependency candidates to evaluate before implementation.
- Governance boundaries for client/domain, environment, visibility, access
  policy, and Public View.
- Separation plan so this work can mature before UI integration.

## Out Of Scope

- Source code implementation.
- Frontend integration.
- Backend route creation.
- Database migrations.
- Figma file creation until the written architecture is reviewed.
- GitHub Issue or PR creation until the planning artifact is approved.
- LLM-local model installation or training.
- Any change to the current module roadmap, navigation scope, or Assets work in
  progress.

## Allowed Files Or Areas

- `docs/agent/TASK_CONTRACT_WORKBENCH_ASSISTANT_PLANNING.md`
- `docs/agent/assistant-planning/`

## Protected Files Or Areas

- `frontend/src/modules/assets/AssetsLibraryView.tsx`
- `frontend/src/app/AppFunctionalAssets.test.tsx`
- `frontend/scripts/functional-assets-browser.mjs`
- `OTM_RESOURCES/`
- `outputs/`
- active module implementation files under `src/`, `frontend/src/`, and
  `tests/`
- active roadmap/governance controls unless the user explicitly approves moving
  this assistant from planning into the main roadmap

## Acceptance Criteria

- The assistant is documented as a local-first, lightweight, specialist tool,
  not a generic local LLM.
- Stack recommendations are compatible with FastAPI, SQLAlchemy, SQLite,
  React/Vite, React Query, React Router, and lucide-react.
- Diagrams cover target architecture, tool routing, indexing, SQL assistance,
  Oracle documentation lookup, and UI entry behavior.
- Planning explicitly protects client/domain, environment, and visibility scope.
- Planning identifies what should be installed or evaluated later without
  installing dependencies prematurely.
- The documentation can be reviewed independently from the current module
  roadmap.

## Validation Plan

- Documentation consistency review.
- Link/path review for newly created planning files.
- `git status --short` review to confirm only planning docs changed.
- No backend, frontend, build, or browser QA is required because this is a
  planning-only slice.

## Risks

- The assistant could accidentally become a generic chatbot and lose trust.
- Oracle documentation lookup can create cost and freshness risks if not cached
  and source-bound.
- SQL generation can create unsafe or misleading outputs if it is not grounded
  in the Data Dictionary and approved query patterns.
- The floating assistant UI could interfere with dense module screens if its
  open/closed states are not designed carefully.
- If this is added to the main roadmap too early, it may distract from current
  module completion.

## Challenge Notes

The final solution should not depend on a heavyweight local LLM. The target
architecture should use local structured knowledge, search, rules, templates,
and source citations first. Optional AI or web/API calls should be controlled
tools, not the foundation.

## Decision

Proceed with isolated planning documentation under
`docs/agent/assistant-planning/`. Do not modify implementation files or active
roadmap controls until the user approves the planning artifact and explicitly
promotes the assistant into delivery scope.
