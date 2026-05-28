# Workbench Assistant Stack Decision Matrix

## Stack Goal

The final stack should stay light enough for normal consultant laptops while
remaining compatible with the existing OTM Workbench architecture.

Current repository baseline:

```text
Backend: Python 3.12, FastAPI, SQLAlchemy, Alembic, SQLite, httpx, Pydantic
Frontend: React, Vite, TypeScript, React Query, React Router, lucide-react
Testing: pytest, Vitest, Playwright scripts
```

## Recommended Target Stack

```text
Backend: existing FastAPI app, new assistant module
Storage: SQLite first, SQLAlchemy models, Alembic migrations when implemented
Search: SQLite FTS5/BM25 local index
Matching: RapidFuzz or equivalent fuzzy matching
Classification: deterministic rules first, optional small scikit-learn model
Web/API: httpx, official-source allowlist, local cache
Frontend: React/Vite assistant components inside WorkbenchShell
Icons: lucide-react plus custom bitmap/SVG launcher asset if needed
AI: optional remote adapter, disabled by default in the core architecture
```

## Decision Matrix

| Area | Option | Pros | Cons | Recommendation |
|---|---|---|---|---|
| Backend runtime | Existing FastAPI app | aligns with repo, low operational overhead | adds module to main app later | recommended |
| Backend runtime | Separate assistant service | isolated experimentation | more ports, auth, deployment, integration | not first choice |
| Storage | SQLite | local-first, already used, low setup | single-user/local constraints | recommended baseline |
| Storage | Postgres | stronger search/vector options | install/admin overhead | future path only |
| Search | SQLite FTS5 | light, local, no service | less advanced ranking | recommended baseline |
| Search | Tantivy | strong Rust-backed search | extra package/runtime complexity | evaluate later |
| Search | Meilisearch | good UX search | separate service to install | not ideal for "any computer" |
| Vector search | pgvector/Qdrant | better semantic search | more dependencies and tuning | future optional |
| Intent routing | Rules + synonyms | transparent, lightweight | needs curated vocabulary | recommended baseline |
| Intent routing | Small ML classifier | lightweight after training | needs labeled examples | phase after corpus exists |
| LLM local | small local model | offline generation | weak quality or hardware pain | avoid as foundation |
| LLM remote | API adapter | strong summaries/explanations | cost and network dependency | optional tool |
| Oracle docs | live lookup + cache | fresh official source | cost/network/freshness control needed | recommended controlled tool |
| Oracle docs | full local mirror | offline | legal/freshness/storage concerns | avoid |

## Dependency Candidates

These are candidates, not immediate install requirements.

### Already Present Or Aligned

- `fastapi`
- `sqlalchemy`
- `alembic`
- `httpx`
- `pydantic`
- `react`
- `vite`
- `@tanstack/react-query`
- `react-router-dom`
- `lucide-react`
- `pytest`
- `vitest`
- `playwright`

### Candidate Python Additions

| Package | Use | Notes |
|---|---|---|
| `rapidfuzz` | fuzzy matching for file/template/table names | low weight |
| `beautifulsoup4` | parse official docs pages when permitted | optional |
| `lxml` | robust HTML/XML parsing | optional, heavier than bs4 |
| `scikit-learn` | small intent/ranking classifier | optional later |
| `joblib` | persist small ML models | only if classifier is added |
| `pypdf` or `pdfplumber` | ingest PDF docs | use only if assistant indexes PDFs |
| `markdown-it-py` | structured Markdown parsing | optional |

### Candidate Frontend Additions

Avoid adding new UI frameworks. The assistant can use existing React, CSS, and
lucide-react.

Potential later additions:

| Package | Use | Notes |
|---|---|---|
| `@floating-ui/react` | robust floating panel positioning | optional |
| `cmdk` | command/search palette patterns | optional, only if aligned visually |

## What Not To Install By Default

- Local LLM runtimes as required dependencies.
- GPU-specific packages.
- Elasticsearch/OpenSearch for local consultant machines.
- A separate vector database service for the baseline.
- Browser automation dependencies beyond the existing Playwright setup unless
  Oracle docs lookup requires a verified path.

## Packaging Direction

The solution should first fit the current local web-app model:

```text
local FastAPI backend
local Vite/React frontend
SQLite database
browser-based Workbench UI
```

Future desktop packaging can wrap the same architecture rather than replacing
it. If a desktop wrapper is later desired, evaluate:

- Tauri: lighter footprint, Rust toolchain requirement.
- Electron: larger footprint, easier ecosystem.
- Native shortcut/launcher: simplest path for Windows users.

Do not choose desktop packaging until the assistant behavior and UI prove
valuable in the existing local web app.
