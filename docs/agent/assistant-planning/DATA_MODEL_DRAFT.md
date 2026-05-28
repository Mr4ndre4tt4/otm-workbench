# Workbench Assistant Data Model Draft

## Purpose

This document proposes conceptual assistant data models for future
implementation. It is intentionally database-oriented but not yet an Alembic
migration or SQLAlchemy implementation.

## Model Groups

```text
source catalog
source chunks and FTS
saved query library
join patterns
Oracle docs cache
assistant sessions and messages
assistant citations/actions
index health and failures
```

## Source Catalog

### `assistant_sources`

Purpose:

Stores every searchable source known to the assistant.

Fields:

```text
id
source_type
title
description
path_or_url
module_id
route_id
project_id
profile_id
domain_name
environment_name
visibility
access_policy_id
status
version_label
current_version
source_hash
indexed_at
expires_at
created_at
updated_at
```

Notes:

- `source_hash` supports changed-source reindexing.
- `visibility`, `domain_name`, and environment fields are mandatory for
  operational/private sources.
- Public/shared technical sources should be explicit, not null-by-accident.

### `assistant_source_chunks`

Purpose:

Stores searchable chunks extracted from sources.

Fields:

```text
id
source_id
heading
body
normalized_terms
rank_weight
line_start
line_end
source_anchor
created_at
```

### `assistant_source_tags`

Purpose:

Adds controlled tags and synonyms.

Fields:

```text
id
source_id
tag
tag_type
```

## Saved Query Library

### `assistant_saved_queries`

Purpose:

Stores approved, draft, and retired SQL examples.

Fields:

```text
id
name
description
sql_text
module_id
status
visibility
project_id
profile_id
domain_name
environment_name
access_policy_id
created_by
reviewed_by
reviewed_at
created_at
updated_at
```

Status values:

```text
draft
approved
retired
```

### `assistant_saved_query_tables`

Purpose:

Records table usage for search and validation.

Fields:

```text
id
query_id
table_name
alias
role
```

### `assistant_saved_query_columns`

Purpose:

Records column usage for search and validation.

Fields:

```text
id
query_id
table_name
column_name
alias
role
```

## Join Pattern Library

### `assistant_join_patterns`

Purpose:

Stores validated or curated join relationships for SQL helper drafting.

Fields:

```text
id
name
left_table
left_column
right_table
right_column
join_type
business_meaning
confidence
source_type
source_id
validated_by
validated_at
created_at
updated_at
```

Join type values:

```text
inner
left
exists
```

Confidence values:

```text
high
medium
low
```

## Oracle Docs Cache

### `assistant_oracle_doc_cache`

Purpose:

Stores official Oracle documentation lookup results.

Fields:

```text
id
query_text
normalized_query
provider
url
title
snippet
summary
official_source
source_hash
fetched_at
expires_at
created_at
updated_at
```

Rules:

- `official_source` must be true for authoritative Oracle answers.
- expired records can still be shown as cached if the UI labels them clearly.

## Assistant Sessions

### `assistant_sessions`

Purpose:

Stores local assistant session context when conversation history is enabled.

Fields:

```text
id
user_id
route
module_id
project_id
profile_id
domain_name
environment_name
visibility
created_at
updated_at
```

### `assistant_messages`

Purpose:

Stores user and assistant messages when history is enabled.

Fields:

```text
id
session_id
role
content
answer_type
confidence
source_mode
cost_level
created_at
```

Role values:

```text
user
assistant
system
```

### `assistant_message_citations`

Purpose:

Links assistant messages to source records.

Fields:

```text
id
message_id
source_id
chunk_id
citation_label
created_at
```

## Index Health

### `assistant_index_runs`

Purpose:

Tracks indexing runs and failures.

Fields:

```text
id
run_type
status
started_at
finished_at
source_count
chunk_count
failure_count
created_by
```

### `assistant_index_failures`

Purpose:

Records source-specific indexing failures.

Fields:

```text
id
run_id
source_ref
source_type
error_code
error_message
created_at
```

## FTS Tables

The implementation should evaluate either:

```text
assistant_source_chunks_fts
```

or an external-content FTS5 table linked to `assistant_source_chunks`.

Required indexed fields:

```text
heading
body
normalized_terms
```

## Migration Cautions

- Keep FTS creation compatible with SQLite.
- Do not require Postgres extensions in the baseline.
- Do not store real client secrets or credentials.
- Do not duplicate large binary assets in assistant tables.
- Store paths and metadata, not file copies, unless a future cache design
  explicitly requires it.
