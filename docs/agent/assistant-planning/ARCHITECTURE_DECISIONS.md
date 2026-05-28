# Workbench Assistant Architecture Decisions

## Purpose

This document records proposed architecture decisions for the Workbench
Assistant. These decisions are draft until the user promotes the assistant from
planning into active delivery scope.

## ADR-WA-001: Assistant Is Embedded, Not A Top-Level Module

Status: proposed

Decision:

The assistant should be exposed through a lower-right floating launcher and an
open side panel inside the existing Workbench shell. It should not appear as a
top-level navigation module in the current UI phase.

Reason:

The assistant is a cross-cutting utility for consultants. A top-level module
would compete with the current module roadmap and make the assistant feel like
a destination rather than contextual help.

Implications:

- mount later inside `WorkbenchShell`;
- use current route/module/context for suggestions;
- do not alter backend top-level navigation until explicitly approved;
- test against dense module screens to ensure the launcher does not obstruct
  primary actions.

## ADR-WA-002: Local Structured Search Is The Foundation

Status: proposed

Decision:

The assistant should use local structured sources, SQLite FTS5, metadata
ranking, and deterministic tools as the baseline. Heavy local LLMs are not part
of the baseline architecture.

Reason:

The assistant must run on common consultant machines. Most required behaviors
are retrieval, filtering, navigation, citation, and template-guided SQL drafting
rather than open-ended reasoning.

Implications:

- first implementation should build source index before chat UI depth;
- local search must be source-bound and scope-aware;
- optional AI can be added later without changing the core contract.

## ADR-WA-003: FastAPI Module In Existing Backend

Status: proposed

Decision:

Implement the assistant as a future module inside the existing FastAPI backend,
not as a separate service.

Reason:

The existing backend already owns authentication context, permissions, module
metadata, Data Dictionary access, artifacts, evidence, and SQLite persistence.
A separate assistant service would duplicate auth and scope logic.

Implications:

- future package path: `src/otm_workbench/assistant/`;
- future routes under `/api/v1/assistant`;
- reuse SQLAlchemy session and platform dependencies;
- keep assistant optional until integrated.

## ADR-WA-004: SQLite First, Postgres Later If Needed

Status: proposed

Decision:

Use SQLite for the first local assistant store and index. Postgres is a future
path only if multi-user/shared deployment or advanced search demands it.

Reason:

The Workbench is currently local-first and already uses SQLite by default.
SQLite FTS5 is sufficient for the first source index and avoids extra services.

Implications:

- model index tables through SQLAlchemy;
- use FTS5 for local search where available;
- design migration path without requiring Postgres-specific features.

## ADR-WA-005: SQL Helper Is Select-Only And Draft-Only

Status: proposed

Decision:

The first SQL Helper design supports only `select` SQL drafts and pasted
`select` explanations. It rejects mutating SQL requests.

Reason:

The assistant is for consultant support and analysis, not direct database
mutation. Mutating SQL creates high risk and should require a separate DBA-only
design if ever needed.

Implications:

- reject `update`, `delete`, `insert`, `merge`, `alter`, `drop`, and DDL;
- mark output as draft;
- cite Data Dictionary and query pattern sources;
- ask clarification when joins are ambiguous.

## ADR-WA-006: Oracle Docs Lookup Is Explicit And Cache-Aware

Status: proposed

Decision:

Oracle documentation lookup should be a controlled online tool. It should use
official-source allowlists, cache results locally, and show fetch/cache
freshness.

Reason:

Oracle documentation is time-sensitive and external. The assistant must not
pretend stale or unofficial information is current official guidance.

Implications:

- user-facing cost/source mode should show live or cached source;
- responses require official links;
- no official result means no source-backed answer;
- cache expiration and refresh behavior must be designed.

## ADR-WA-007: Response Contract Is Structured

Status: proposed

Decision:

The backend should return structured assistant responses, even if the UI renders
them conversationally.

Reason:

Structured responses make UI states, source citations, actions, cost metadata,
and tests reliable. Free-form text would make safety and rendering harder.

Implications:

- define `answer_type`, `summary`, `steps`, `actions`, `sources`,
  `confidence`, `source_mode`, `cost_level`, and `scope`;
- UI renders typed blocks;
- tests assert structure rather than exact prose.

## ADR-WA-008: Optional AI Cannot Be A Source Of Truth

Status: proposed

Decision:

Any future AI adapter can summarize or rewrite source-grounded content, but it
cannot create source truth, bypass scope filtering, or invent SQL/Data
Dictionary facts.

Reason:

The assistant's trust model depends on sources and permissions, not model
confidence.

Implications:

- AI adapter sits after retrieval and scope filtering;
- AI output must reference supplied sources;
- AI can be disabled without breaking core assistant behavior.
