# Workbench Assistant Environment Baseline

## Purpose

This document records the local environment capabilities checked during
assistant planning. It helps decide which software needs to be installed later
and which capabilities are already available.

## Check Date

2026-05-28

## Commands Run

```powershell
python --version
node --version
npm --version
@'
import sqlite3
print('sqlite', sqlite3.sqlite_version)
con = sqlite3.connect(':memory:')
con.execute('create virtual table docs using fts5(title, body)')
con.execute('insert into docs(title, body) values (?, ?)', ('Assistant', 'OTM Workbench local search'))
rows = con.execute("select title from docs where docs match 'local'").fetchall()
print('fts5', 'ok' if rows == [('Assistant',)] else rows)
'@ | python -
```

## Results

```text
Python: 3.13.7
Node.js: v25.9.0
npm: 11.12.1
SQLite: 3.50.4
SQLite FTS5: ok
```

## Interpretation

SQLite FTS5 is already available in the local Python SQLite build. This supports
the recommended local-first search baseline without installing Elasticsearch,
OpenSearch, Meilisearch, Qdrant, or another search service.

The assistant planning stack can keep this baseline:

```text
FastAPI
SQLAlchemy
SQLite
SQLite FTS5
React/Vite
React Query
React Router
```

## Installation Impact

No installation is required for the first planned search foundation capability.

Potential future additions remain conditional:

- RapidFuzz only if FTS and normalized matching are not enough for table/file
  names;
- document parsers only when PDF/HTML ingestion is in scope;
- Oracle docs lookup provider only when live lookup is implemented;
- scikit-learn only after labeled assistant questions exist;
- optional AI adapter only after local source-bound behavior is stable.

## Caveats

- The project `pyproject.toml` requires Python `>=3.12`; the checked Python
  version satisfies that requirement.
- Implementation should still verify FTS5 in the runtime environment used by
  packaged consultants, not only this development machine.
- Node/npm versions are newer than the minimum implied by the current frontend
  stack; implementation should continue using the project's lockfile and
  existing package manager workflow.
