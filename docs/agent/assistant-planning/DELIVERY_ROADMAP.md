# Workbench Assistant Delivery Roadmap

## Purpose

This roadmap defines how the Workbench Assistant can mature as a separate track
before it is integrated into the active OTM Workbench UI. It intentionally does
not change the current module delivery roadmap.

## Delivery Principle

The assistant should be delivered as a sequence of small, reversible slices:

```text
knowledge foundation
  -> local search
  -> contextual UI shell
  -> Workbench help
  -> finder
  -> SQL helper
  -> Oracle docs lookup
  -> optional AI enhancement
```

Each slice must prove value without requiring the later slices.

## Phase 0: Planning And Design

Status: current phase.

Goals:

- define product boundary;
- define stack;
- define UX entry and panel states;
- define source index model;
- define SQL helper guardrails;
- define Oracle docs lookup constraints;
- prepare diagram and Figma/FigJam plan.

Exit criteria:

- planning packet reviewed;
- unresolved decisions listed;
- user approves promotion into implementation planning;
- no active module roadmap conflict.

Artifacts:

- `docs/agent/assistant-planning/`
- `docs/superpowers/specs/2026-05-28-workbench-assistant-design.md`

## Phase 1: Knowledge Foundation

Goal:

Create the local source catalog and indexing foundation without any visible
assistant UI.

Candidate scope:

- assistant source records;
- source chunk records;
- SQLite FTS5 index;
- Workbench Markdown/help indexing;
- Data Dictionary availability check;
- scoped source filtering rules;
- index health endpoint for authorized users.

Acceptance:

- local docs can be indexed and searched;
- private/scoped records are filtered before snippets;
- Data Dictionary source health is visible;
- no frontend integration required.

## Phase 2: Contextual Assistant Shell

Goal:

Add the closed/open assistant UI shell with no complex intelligence yet.

Candidate scope:

- lower-right robot launcher;
- right-side assistant panel;
- context strip;
- quick action skeleton;
- local-only status indicator;
- close/focus/keyboard behavior;
- empty, loading, blocked, offline states.

Acceptance:

- launcher does not interfere with dense module screens;
- panel reads current module/route/context;
- accessibility baseline passes focused tests;
- no Oracle/web/AI dependency.

## Phase 3: Workbench Help Tool

Goal:

Answer "how do I use this screen/module?" from local Workbench help and route
metadata.

Candidate scope:

- `workbench_help` intent;
- route/module help chunks;
- contextual quick action;
- answer contract with steps, sources, actions, and confidence.

Acceptance:

- current screen help returns source-bound steps;
- irrelevant modules are ranked lower;
- unknown screen returns a safe no-help state;
- Public View receives only public help.

## Phase 4: Finder Tool

Goal:

Find templates, workbooks, files, saved queries, artifacts, and evidence from
the scoped local catalog.

Candidate scope:

- `find_artifact` intent;
- source-type filters;
- result cards;
- open/copy route actions;
- no-access-safe messaging.

Acceptance:

- scoped consultant sees allowed records;
- non-authorized user receives no leaked title/path/snippet;
- current domain/environment results rank higher;
- archived/retired records are hidden by default.

## Phase 5: SQL Helper

Goal:

Draft safe select-only OTM SQL using Data Dictionary, approved query examples,
and explicit join patterns.

Candidate scope:

- table and column resolution;
- saved query search;
- join pattern records;
- query templates;
- SQL draft response;
- explain pasted SQL;
- unsafe mutation rejection.

Acceptance:

- exact table lookup works;
- ambiguous table families trigger clarification;
- unknown columns are not silently generated;
- approved query examples influence ranking;
- generated SQL is marked as draft and source-cited.

## Phase 6: Oracle Docs Lookup

Goal:

Add controlled live lookup against official Oracle documentation with local
cache.

Candidate scope:

- explicit Oracle Docs mode;
- official-source allowlist;
- cache records with freshness;
- short source-bound summary;
- offline and expired-cache behavior.

Acceptance:

- responses include official links;
- cached responses show timestamp;
- no official source means no fabricated answer;
- live lookup is visible as a web/cost-bearing operation.

## Phase 7: Optional AI Enhancement

Goal:

Add optional AI assistance only after local source-bound behavior is stable.

Candidate scope:

- feature flag;
- provider adapter;
- prompt templates that require sources;
- answer rewriting/summarization only;
- cost-level metadata.

Acceptance:

- AI can be disabled without breaking assistant features;
- AI cannot bypass scope guard;
- AI cannot answer Oracle docs questions without official sources;
- AI cannot invent SQL tables/columns.

## Phase 8: Desktop Packaging Evaluation

Goal:

Evaluate whether consultants need a desktop-style wrapper after the web-local
assistant proves useful.

Candidate scope:

- Windows shortcut/local launcher;
- Tauri or Electron feasibility review;
- installer footprint comparison;
- auto-start and update implications.

Acceptance:

- packaging choice does not change assistant architecture;
- local web mode remains supported;
- no heavyweight runtime is introduced only for packaging.

## Integration Gate

The assistant should not enter the main product roadmap until:

- Phase 0 design is accepted;
- Phase 1 knowledge foundation is technically feasible;
- UI entry has Michelangelo/Figma review;
- scope guard behavior is proven;
- SQL helper safety rules are accepted;
- current module delivery has room for a cross-cutting slice.

## Recommended First Implementation Slice Later

When implementation is approved, start with Phase 1, not the robot UI.

Reason:

- the assistant's value depends on local sources and scope-safe search;
- UI without reliable sources would become a hollow chatbot shell;
- source indexing can be built and tested without disrupting module screens.
