# Workbench Assistant Installation Evaluation Plan

## Purpose

The user authorized downloads/installations when needed, but the assistant
planning track should avoid installing packages before the design justifies
them. This document defines how to evaluate software additions safely.

## Current Decision

Do not install anything during planning.

Reason:

The current repository already has enough stack support for the planned
baseline:

```text
FastAPI
SQLAlchemy
SQLite
httpx
React/Vite
React Query
React Router
lucide-react
pytest/Vitest/Playwright
```

SQLite FTS5 should be evaluated first because it may already be available in
the local Python SQLite build.

## Baseline Check Result

The local environment was checked on 2026-05-28:

```text
Python: 3.13.7
Node.js: v25.9.0
npm: 11.12.1
SQLite: 3.50.4
SQLite FTS5: ok
```

See `ENVIRONMENT_BASELINE.md`.

Decision:

No search service or search package needs to be installed for the first planned
local source index. SQLite FTS5 is available and should remain the baseline.

## Evaluation Order

### Step 1: Verify SQLite FTS5

Command concept:

```powershell
python - <<'PY'
import sqlite3
con = sqlite3.connect(':memory:')
con.execute('create virtual table docs using fts5(title, body)')
print('fts5-ok')
PY
```

Decision:

- FTS5 works in the current local environment, so do not add a search server;
- if FTS5 is unavailable, evaluate fallback options.

### Step 2: Evaluate RapidFuzz

Use only if table/file/template name matching needs fuzzy matching beyond FTS.

Criteria:

- Windows install succeeds;
- dependency footprint is small;
- tests prove better matching than simple normalization.

### Step 3: Evaluate Document Parsers

Only add parsers for source types that are in scope.

Candidates:

- `pypdf` for basic PDF text;
- `pdfplumber` for richer PDF/table extraction;
- `beautifulsoup4` for HTML parsing;
- `lxml` only when needed.

Criteria:

- parser handles representative synthetic files;
- parser failures are isolated;
- parser does not become runtime dependency for normal chat path.

### Step 4: Evaluate Oracle Docs Lookup Provider

Options:

- direct official docs fetch with `httpx`;
- search API provider with official-domain filter;
- browser automation only for pages that require it.

Criteria:

- official links returned;
- cacheable result;
- sanitized query;
- predictable cost;
- failure fallback.

### Step 5: Evaluate Small ML Classifier

Only after assistant questions are collected.

Candidates:

- `scikit-learn`;
- persisted model with `joblib`.

Criteria:

- improves intent classification measurably;
- remains optional;
- does not require heavy model files.

### Step 6: Evaluate Optional AI Adapter

Only after local retrieval and SQL helper are stable.

Criteria:

- disabled by default;
- source-bound prompts;
- no scope bypass;
- cost metadata;
- clear fallback when unavailable.

## Rejected Baseline Dependencies

Do not add these to baseline:

```text
local LLM runtimes
GPU-specific packages
Elasticsearch/OpenSearch
Meilisearch service
Qdrant service
Electron/Tauri packaging
large embedding model files
```

These may be revisited only with a specific approved problem they solve.

## Evaluation Record Template

Use this template for future dependency decisions:

```text
Dependency:
Capability:
Why existing stack is insufficient:
Install footprint:
Windows behavior:
Alternatives:
Tests added:
Decision:
```

## Current Recommended Baseline

```text
No new package until implementation starts.
First technical check completed: SQLite FTS5 is available.
First likely addition: RapidFuzz, only if needed.
```
