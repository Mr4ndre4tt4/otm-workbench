# Workbench Assistant Design

**Status:** draft planning design
**Date:** 2026-05-28
**Scope:** lightweight embedded assistant for OTM Workbench consultants

## Problem

OTM Workbench is growing into a local-first consultant workbench with module
flows for master data, rates, load planning, integration, order release, assets,
and settings. Consultants need fast answers to operational questions such as:

- where to find a template, workbook, query, artifact, or evidence item;
- how to use a Workbench screen or module;
- which route or action supports a task;
- how to draft a safe OTM SQL query from Data Dictionary knowledge;
- where official Oracle documentation answers a technical question.

A generic chatbot would be too broad, too expensive, and too hard to trust. A
heavy local LLM would also make the tool difficult to run on common consultant
machines.

## Design Decision

Design a **Workbench Assistant** as a lightweight specialist assistant embedded
in the Workbench shell.

The assistant is:

```text
local-first
source-bound
permission-aware
context-aware
tool-based
lightweight
optionally online for Oracle docs
optionally AI-enhanced later
```

The assistant is not:

```text
a top-level module
a generic LLM chatbot
a project-management dashboard
a replacement for Data Dictionary validation
a shortcut around client/domain and environment boundaries
```

## UX Entry Point

The assistant should appear as a small lower-right truck-driver robot launcher.

Closed state:

```text
small floating button
available across Workbench routes
does not cover dense work areas
shows a concise accessible label and tooltip
```

Open state:

```text
right-side assistant panel or large drawer
shows current context
offers contextual quick actions
supports source/citation rendering
supports SQL draft review
supports Oracle docs lookup result state
supports blocked/offline/clarification states
```

The robot identity can be friendly in the launcher. The open panel should stay
operational, dense, and consultant-focused.

## Target Architecture

The architecture is documented in:

- `docs/agent/assistant-planning/TARGET_ARCHITECTURE.md`
- `docs/agent/assistant-planning/ARCHITECTURE_DECISIONS.md`
- `docs/agent/assistant-planning/FLOWS.md`
- `docs/agent/assistant-planning/STACK_DECISION_MATRIX.md`
- `docs/agent/assistant-planning/INSTALLATION_CANDIDATES.md`
- `docs/agent/assistant-planning/UI_EXPERIENCE_SPEC.md`
- `docs/agent/assistant-planning/SQL_HELPER_DESIGN.md`
- `docs/agent/assistant-planning/SOURCE_INDEX_DESIGN.md`
- `docs/agent/assistant-planning/DATA_MODEL_DRAFT.md`
- `docs/agent/assistant-planning/TOOL_CONTRACTS.md`
- `docs/agent/assistant-planning/RESPONSE_CONTRACT.md`
- `docs/agent/assistant-planning/ORACLE_DOCS_CONNECTOR_POLICY.md`
- `docs/agent/assistant-planning/PRIVACY_AND_HISTORY_POLICY.md`
- `docs/agent/assistant-planning/QUERY_CORPUS_STRATEGY.md`
- `docs/agent/assistant-planning/DIAGRAM_PLAN.md`
- `docs/agent/assistant-planning/DELIVERY_ROADMAP.md`
- `docs/agent/assistant-planning/TEST_AND_VALIDATION_STRATEGY.md`
- `docs/agent/assistant-planning/GOVERNANCE_AND_RISKS.md`
- `docs/agent/assistant-planning/FIGMA_FIGJAM_BRIEF.md`
- `docs/agent/assistant-planning/VISUAL_CALIBRATION_QUESTIONNAIRE.md`
- `docs/agent/assistant-planning/FIGJAM_TECHNICAL_BOARD_MANIFEST.md`
- `docs/agent/assistant-planning/FIGJAM_CREATION_REPORT.md`
- `docs/agent/assistant-planning/FIGMA_WIREFRAME_MANIFEST.md`
- `docs/agent/assistant-planning/FIGMA_WIREFRAME_CREATION_REPORT.md`
- `docs/agent/assistant-planning/INSTALLATION_EVALUATION_PLAN.md`
- `docs/agent/assistant-planning/ENVIRONMENT_BASELINE.md`
- `docs/agent/assistant-planning/PLANNING_REVIEW_CHECKLIST.md`
- `docs/agent/assistant-planning/OPEN_DECISIONS.md`

Recommended component shape:

```text
Assistant UI
  -> Assistant API
    -> context and permission guard
    -> intent router
    -> Workbench help tool
    -> artifact/template/query finder
    -> SQL helper
    -> Oracle docs connector
    -> navigation tool
    -> source and citation layer
```

## Stack Direction

The stack should align with the current repository:

```text
Backend: FastAPI module inside existing app
Storage: SQLite via SQLAlchemy
Search: SQLite FTS5/BM25
Matching: rules, synonyms, and optional RapidFuzz
Classification: deterministic first, optional small model later
Frontend: React/Vite component mounted in WorkbenchShell
Online lookup: httpx-based Oracle docs connector with cache
AI: optional remote adapter only after source-bound local behavior works
```

No heavyweight local LLM is required for the target architecture.

## Core Tools

### Workbench Help

Answers how to use modules, screens, actions, validation states, and route
recovery paths from local Workbench documentation and backend-owned metadata.

### Finder

Finds templates, Excel workbooks, queries, evidence, artifacts, and supporting
docs from a scoped local source catalog.

### Navigation

Suggests Workbench routes and actions using backend-owned navigation and
capability metadata.

### SQL Helper

Drafts OTM SQL using:

- Data Dictionary tables and columns;
- approved saved query examples;
- explicit join patterns;
- templates;
- source citations;
- confidence and assumptions.

The SQL helper should ask a focused clarification when table or join intent is
ambiguous.

### Oracle Docs Connector

Looks up official Oracle documentation only when needed, returns source links,
stores a local cache record, and distinguishes official source content from
Workbench inference.

## Scope And Access Rules

Every assistant operation must respect:

```text
user and role
project/profile
client/domain
environment
visibility
access policy
Public View boundary
current route/module context
```

Denied private results must not leak titles, snippets, paths, client names, or
file names.

## Response Contract

Assistant answers should be structured internally even when rendered as
conversation:

```json
{
  "answer_type": "help|search_results|sql_draft|oracle_docs|navigation|blocked",
  "summary": "...",
  "steps": [],
  "actions": [],
  "sources": [],
  "confidence": "high|medium|low",
  "source_mode": "indexed|cached|live_official|generated_draft",
  "cost_level": "local|web|ai|web_plus_ai",
  "scope": {
    "project_id": "...",
    "domain_name": "...",
    "environment_name": "...",
    "visibility": "..."
  }
}
```

## Out Of Scope For This Design

- Implementation code.
- UI integration.
- Database migrations.
- Figma artifact creation.
- Installing new packages.
- Adding GitHub tracking.
- Changing active module roadmap.

## Acceptance Criteria For Planning

- The assistant is defined as a separate future planning track.
- The target stack is compatible with the current OTM Workbench architecture.
- The design avoids heavyweight local AI as a foundation.
- The SQL helper is grounded in Data Dictionary and approved query patterns.
- Oracle docs lookup is source-linked and cache-aware.
- The floating launcher/open panel UX is documented.
- Security and scope boundaries are explicit.

## Next Step

Review the planning packet and decide whether to:

1. expand the diagrams into Figma/FigJam;
2. refine the SQL helper design in more depth;
3. refine the assistant UI states and interaction model;
4. create an implementation plan after the design is approved.
