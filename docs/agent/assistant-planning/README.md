# Workbench Assistant Planning

**Status:** draft planning track
**Date:** 2026-05-28
**Owner:** separate exploration track, not active module delivery

## Purpose

The Workbench Assistant is a future embedded assistant for OTM Workbench
consultants. It should appear as a small truck-driver robot button in the lower
right corner of the Workbench shell. When opened, it provides contextual help,
local search, template/file discovery, Data Dictionary-backed SQL assistance,
saved-query reuse, and official Oracle documentation lookup.

The assistant is not intended to be a generic reasoning agent. It should be a
lightweight specialist layer that finds, validates, and points to sources.

## Product Position

The target product shape is:

```text
Workbench Assistant
  local-first
  consultant-focused
  source-bound
  permission-aware
  context-aware
  lightweight on disk and CPU
  optional web/API for Oracle documentation
  optional AI only as an enhancement
```

The assistant should help consultants move faster inside the Workbench without
turning the Workbench into a project-management system or a generic chatbot.

## Non-Goals

- Do not run a heavyweight local LLM as the baseline.
- Do not train a broad machine-learning model before proving that structured
  search, rules, and query templates are insufficient.
- Do not create a new top-level module for the current UI phase.
- Do not expose private client data through Public View or cross-client search.
- Do not answer Oracle technical questions without source links.
- Do not generate SQL without Data Dictionary grounding and confidence labels.

## Planning Packet

- [Target Architecture](TARGET_ARCHITECTURE.md)
- [Architecture Decisions](ARCHITECTURE_DECISIONS.md)
- [Stack Decision Matrix](STACK_DECISION_MATRIX.md)
- [Macroflows And Microflows](FLOWS.md)
- [UI Experience Spec](UI_EXPERIENCE_SPEC.md)
- [SQL Helper Design](SQL_HELPER_DESIGN.md)
- [Source Index Design](SOURCE_INDEX_DESIGN.md)
- [Data Model Draft](DATA_MODEL_DRAFT.md)
- [Tool Contracts](TOOL_CONTRACTS.md)
- [Response Contract](RESPONSE_CONTRACT.md)
- [Oracle Docs Connector Policy](ORACLE_DOCS_CONNECTOR_POLICY.md)
- [Privacy And History Policy](PRIVACY_AND_HISTORY_POLICY.md)
- [Query Corpus Strategy](QUERY_CORPUS_STRATEGY.md)
- [Diagram Plan](DIAGRAM_PLAN.md)
- [Delivery Roadmap](DELIVERY_ROADMAP.md)
- [Test And Validation Strategy](TEST_AND_VALIDATION_STRATEGY.md)
- [Governance And Risks](GOVERNANCE_AND_RISKS.md)
- [Figma And FigJam Brief](FIGMA_FIGJAM_BRIEF.md)
- [Visual Calibration Questionnaire](VISUAL_CALIBRATION_QUESTIONNAIRE.md)
- [FigJam Technical Board Manifest](FIGJAM_TECHNICAL_BOARD_MANIFEST.md)
- [FigJam Creation Report](FIGJAM_CREATION_REPORT.md)
- [Figma Wireframe Manifest](FIGMA_WIREFRAME_MANIFEST.md)
- [Figma Wireframe Creation Report](FIGMA_WIREFRAME_CREATION_REPORT.md)
- [Installation And Software Candidates](INSTALLATION_CANDIDATES.md)
- [Installation Evaluation Plan](INSTALLATION_EVALUATION_PLAN.md)
- [Environment Baseline](ENVIRONMENT_BASELINE.md)
- [Planning Review Checklist](PLANNING_REVIEW_CHECKLIST.md)
- [Open Decisions](OPEN_DECISIONS.md)

## Executable Plans

- [Source Index Foundation](../../superpowers/plans/2026-05-28-workbench-assistant-source-index-foundation.md)
  defines the first backend-only implementation slice. It keeps the assistant
  outside the main UI navigation while establishing local source metadata,
  SQLite FTS search, scoped result filtering, and API tests.
- [SQL Helper Foundation](../../superpowers/plans/2026-05-28-workbench-assistant-sql-helper-foundation.md)
  defines the first deterministic SQL helper slice: SELECT-only safety,
  Data Dictionary-backed table/column validation, simple pasted SELECT
  explanation, and single-table draft responses.
- [Saved Query Corpus Foundation](../../superpowers/plans/2026-05-28-workbench-assistant-saved-query-corpus-foundation.md)
  defines the first trusted-query corpus slice: draft storage, approval
  validation, literal-value guardrails, scoped search, and retired-query hiding.
- [Join Pattern Curation](../../superpowers/plans/2026-05-28-workbench-assistant-join-pattern-curation.md)
  defines the reviewed relationship library slice: draft join patterns,
  Data Dictionary validation, approved saved-query source checks, and
  searchable approved patterns before join SQL generation is allowed.
- [Joined SQL Draft](../../superpowers/plans/2026-05-28-workbench-assistant-joined-sql-draft.md)
  defines the first deterministic two-table SQL generation slice: callers must
  choose an approved join pattern, requested columns are validated through the
  Data Dictionary, and the output is a parameterized SELECT draft only.
- [Oracle Docs Cache](../../superpowers/plans/2026-05-28-workbench-assistant-oracle-docs-cache.md)
  defines the first official-documentation lookup foundation: admin-reviewed
  Oracle documentation links are cached locally, authenticated users can search
  approved records, and live web lookup is blocked until a separate explicit
  connector is implemented.
- [Oracle Lookup Request](../../superpowers/plans/2026-05-28-workbench-assistant-oracle-lookup-request.md)
  defines the explicit web-action preparation slice: user questions are
  sanitized, private terms are removed, official Oracle search links are
  generated, and no network request is executed by the backend.

## Current Assumptions

- Primary users are OTM consultants who use the Workbench frequently during
  implementation, validation, migration, support, and cutover preparation.
- The assistant is embedded in the existing React Workbench shell.
- The backend remains FastAPI and owns assistant routing, permissions,
  citations, and source evaluation.
- SQLite remains the first local storage target, with a future Postgres path if
  the assistant outgrows local single-user data.
- Oracle documentation lookup is a controlled online tool with cache, not a
  continuously synchronized local copy of Oracle docs.

## Review Questions

1. Should the assistant be available in Public View, and if so should it be
   limited to public Workbench help plus official Oracle docs?
2. Should SQL helper output be copy-only, saved as draft query, or both?
3. Should Oracle documentation lookup require an explicit "search web" action
   to make costs and freshness visible?
4. Should assistant search include archived assets, or only active/current
   assets by default?
