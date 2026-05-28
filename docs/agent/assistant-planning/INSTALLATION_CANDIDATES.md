# Workbench Assistant Installation And Software Candidates

## Installation Philosophy

The assistant should not require a heavy local AI stack. The baseline should be
installable wherever OTM Workbench already runs.

Do not install candidate packages until the design is approved and the first
implementation plan identifies exact dependencies.

## Baseline Already Required By OTM Workbench

Backend:

```text
Python 3.12
FastAPI
SQLAlchemy
Alembic
SQLite
httpx
Pydantic
uvicorn
```

Frontend:

```text
Node.js
React
Vite
TypeScript
React Query
React Router
lucide-react
Vitest
Playwright scripts
```

## Candidate Additions By Capability

### Local Search And Matching

Recommended first:

```text
SQLite FTS5
RapidFuzz
```

Rationale:

- SQLite FTS5 keeps search local and service-free.
- RapidFuzz is lightweight and useful for table names, file names, template
  names, and misspelled OTM terms.

### Document Parsing

Only if assistant indexing needs these source types:

```text
openpyxl       already present, Excel workbook metadata/content
pypdf         PDF text extraction
pdfplumber    richer PDF table/text extraction
beautifulsoup4 HTML parsing for cached docs
lxml          robust XML/HTML parsing when needed
```

Keep PDF parsing behind a separate ingestion path so normal assistant runtime
does not become slow.

### Intent Classification

Start without ML:

```text
rules
synonym dictionaries
known module names
known OTM object/table terms
route metadata
```

Potential later:

```text
scikit-learn
joblib
```

Use these only after enough real assistant questions exist to train and test a
small classifier. Do not guess a model before collecting examples.

### Oracle Documentation Lookup

Baseline:

```text
httpx
official-domain allowlist
local cache table
```

Optional:

```text
beautifulsoup4
Playwright only when static HTTP cannot retrieve a needed official page
```

Oracle lookup should be implemented as an explicit online tool with source
links and cache metadata.

### Optional AI Adapter

The core should not require AI. If enabled later:

```text
remote AI provider adapter
feature flag
cost-level metadata
prompt templates
source-grounding checks
```

The AI adapter may help summarize official docs or rewrite local search
results, but it must not be allowed to invent sources or bypass the SQL helper
rules.

## Local Disk Expectations

Expected lightweight baseline:

```text
assistant DB: tens to hundreds of MB
cached docs: depends on Oracle/doc usage
indexed chunks: proportional to Workbench docs, Data Dictionary, query library
no model files required
```

Avoid:

```text
multi-GB local LLM weights
separate search server indexes by default
full Oracle documentation mirrors
```

## Windows Local Runtime Notes

The assistant should work within the current Windows local development/runtime
model:

```text
FastAPI backend process
Vite or built frontend
SQLite database under var/
browser access to local Workbench
```

Future packaging options:

| Packaging | Pros | Cons | Recommendation |
|---|---|---|---|
| Current local web app | matches project today | needs browser/local server | baseline |
| Windows shortcut/launcher | simple user entry | still web app underneath | good later |
| Tauri | lighter desktop wrapper | Rust/toolchain complexity | evaluate later |
| Electron | mature desktop wrapper | heavier disk/RAM | avoid unless needed |

## Candidate Installation Sequence

When implementation begins, evaluate in this order:

1. Use only current dependencies plus SQLite FTS5.
2. Add RapidFuzz if name matching quality needs it.
3. Add document parsers only for source types being indexed.
4. Add Oracle docs parser/cache dependencies only when live lookup is built.
5. Add scikit-learn only after labeled assistant usage examples exist.
6. Add AI provider adapter only after source-bound local behavior is stable.

## Verification Before Installing

Before adding any dependency:

- confirm the capability cannot be done cleanly with existing dependencies;
- check package size and transitive dependencies;
- confirm Windows install behavior;
- add focused tests around the capability;
- record the decision in the assistant planning docs or implementation plan.
