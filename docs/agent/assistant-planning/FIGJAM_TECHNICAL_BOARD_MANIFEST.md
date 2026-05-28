# Workbench Assistant FigJam Technical Board Manifest

## Purpose

This manifest defines the future FigJam technical board for the Workbench
Assistant. It should be created after visual calibration is accepted.

## Board Name

```text
OTM Workbench - Workbench Assistant Technical Architecture
```

## Board Goal

Explain how the assistant works before implementation:

- product boundary;
- local-first architecture;
- source index;
- scope guard;
- SQL helper;
- Oracle docs lookup;
- response contract;
- delivery phases and risks.

## Intended Audience

- product owner;
- future implementation agent;
- frontend engineer;
- backend engineer;
- reviewer checking security/scope risk.

## Section Inventory

### 01 Product Boundary

Purpose:

Show what the assistant is and is not.

Cards:

- embedded Workbench utility;
- lower-right robot launcher;
- contextual right-side panel;
- not a top-level module;
- not a generic chatbot;
- not a local LLM dependency.

### 02 High-Level Architecture

Purpose:

Show the major components and ownership.

Diagram:

```text
Assistant UI
  -> Assistant API
  -> Intent Router
  -> Tools
  -> Source/Citation Layer
  -> Scope Guard
```

Annotations:

- backend owns truth;
- UI renders structured responses;
- optional AI is downstream of retrieval.

### 03 Local Source Index

Purpose:

Show source discovery, chunking, scope metadata, and SQLite FTS5.

Diagram:

```text
source discovered
  -> adapter
  -> chunks
  -> source scope
  -> FTS index
  -> ranked results
```

Key callout:

SQLite FTS5 is already verified in the local environment.

### 04 Scope Guard

Purpose:

Show why filtering happens before snippets.

Diagram:

```text
candidate result
  -> visibility
  -> project/profile
  -> domain
  -> environment
  -> access policy
  -> render or suppress
```

Blocked-state callout:

Denied records must not reveal title, path, snippet, client name, or count.

### 05 Tool Router

Purpose:

Show assistant modes as narrow tools.

Tools:

- Workbench Help;
- Finder;
- Navigation;
- SQL Helper;
- Oracle Docs;
- Clarification.

Each tool should show:

```text
input
source
output
failure state
```

### 06 SQL Helper

Purpose:

Show the most sensitive flow.

Diagram:

```text
question
  -> entity extraction
  -> table resolution
  -> column resolution
  -> saved query match
  -> join pattern
  -> template draft
  -> citations and warnings
```

Callouts:

- select-only;
- draft-only;
- Data Dictionary grounded;
- asks clarification when ambiguous.

### 07 Oracle Docs Connector

Purpose:

Show online lookup and cache.

Diagram:

```text
question
  -> sanitize
  -> cache check
  -> explicit live lookup
  -> official source allowlist
  -> cache result
  -> link + freshness
```

Callouts:

- no private data in external query;
- official link required;
- no official source means no authoritative answer.

### 08 Response Contract

Purpose:

Show structured response object and UI rendering.

Blocks:

- answer type;
- summary;
- blocks;
- actions;
- sources;
- confidence;
- source mode;
- cost level;
- scope.

### 09 UI State Map

Purpose:

Show state transitions without visual polish.

States:

- closed;
- open ready;
- loading;
- answer;
- search results;
- SQL draft;
- Oracle result;
- clarification;
- permission blocked;
- offline limited;
- error.

### 10 Delivery Roadmap

Purpose:

Show separate phased path.

Phases:

0. planning;
1. knowledge foundation;
2. assistant shell;
3. Workbench help;
4. finder;
5. SQL helper;
6. Oracle docs;
7. optional AI;
8. desktop packaging evaluation.

### 11 Risks And Gates

Purpose:

Show stop conditions.

Risks:

- generic chatbot drift;
- private data leakage;
- invented SQL;
- stale Oracle docs;
- hidden API costs;
- UI obstruction.

Gates:

- planning approval;
- source index proof;
- scope guard tests;
- SQL safety acceptance;
- Michelangelo/Figma UI review.

## Visual Style

Use a technical FigJam style:

```text
neutral background
section columns
clear arrows
compact cards
warning callouts for risk
green callouts for accepted principles
blue callouts for proposed architecture
```

## Source Documents

Use these planning files as source:

- `TARGET_ARCHITECTURE.md`
- `SOURCE_INDEX_DESIGN.md`
- `SQL_HELPER_DESIGN.md`
- `ORACLE_DOCS_CONNECTOR_POLICY.md`
- `RESPONSE_CONTRACT.md`
- `DELIVERY_ROADMAP.md`
- `GOVERNANCE_AND_RISKS.md`
- `ENVIRONMENT_BASELINE.md`

## Acceptance Criteria

- Board explains the assistant without reading all docs.
- Board makes scope and privacy boundaries visible.
- SQL helper is visibly constrained and source-grounded.
- Oracle docs lookup is visibly explicit and cache-aware.
- Delivery roadmap is clearly separate from active module delivery.
