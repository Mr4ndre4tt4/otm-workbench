# Workbench Assistant Tool Contracts

## Purpose

The assistant should route requests to narrow tools. This document defines
future tool contracts at a planning level so implementation can remain typed,
testable, and source-bound.

## Shared Tool Input

Every tool receives the same context envelope.

```json
{
  "message": "string",
  "route": "string",
  "module_id": "string",
  "user": {
    "user_id": "string",
    "roles": ["string"],
    "capabilities": ["string"]
  },
  "scope": {
    "project_id": "string",
    "profile_id": "string",
    "domain_name": "string",
    "environment_name": "string",
    "visibility": "PRIVATE|PUBLIC"
  },
  "options": {
    "allow_web": false,
    "allow_ai": false,
    "include_archived": false
  }
}
```

## Shared Tool Output

Every tool returns structured blocks.

```json
{
  "answer_type": "help|search_results|sql_draft|oracle_docs|navigation|blocked|clarification",
  "summary": "string",
  "blocks": [],
  "actions": [],
  "sources": [],
  "confidence": "high|medium|low",
  "source_mode": "indexed|cached|live_official|generated_draft",
  "cost_level": "local|web|ai|web_plus_ai",
  "warnings": []
}
```

## Tool: Workbench Help

Intent:

```text
workbench_help
```

Purpose:

Answer how to use the current screen, module, workflow, action, or validation
state.

Primary sources:

- Workbench help index;
- route metadata;
- module specs;
- backend-owned action labels and disabled reasons.

Output blocks:

```json
[
  {
    "type": "steps",
    "title": "How to use this screen",
    "items": ["string"]
  },
  {
    "type": "related_actions",
    "items": []
  }
]
```

Failure states:

- no help indexed for route;
- route unknown;
- user lacks permission to view the route.

## Tool: Finder

Intent:

```text
find_artifact
```

Purpose:

Find templates, Excel files, saved queries, artifacts, evidence, and supporting
documents inside allowed scope.

Primary sources:

- assistant source index;
- Assets Library;
- artifacts/manifests/evidence;
- saved query library.

Result card:

```json
{
  "title": "string",
  "source_type": "asset|artifact|evidence|saved_query|workbench_doc",
  "module_id": "string",
  "status": "string",
  "version_label": "string",
  "scope": {
    "domain_name": "string",
    "environment_name": "string",
    "visibility": "string"
  },
  "actions": [
    {
      "label": "Open",
      "kind": "route",
      "target": "string"
    }
  ]
}
```

Security rule:

Denied records are suppressed before result shaping.

## Tool: Navigation

Intent:

```text
navigate
```

Purpose:

Tell the consultant where in the Workbench to perform a task and optionally
offer an open-route action.

Primary sources:

- backend navigation contract;
- route metadata;
- module capability metadata;
- current user permissions.

Output action:

```json
{
  "label": "Open Rate batch library",
  "kind": "route",
  "target": "/rates/batches",
  "enabled": true,
  "disabled_reason": null
}
```

## Tool: SQL Helper

Intent:

```text
sql_help
```

Purpose:

Draft safe select-only OTM SQL and explain pasted select queries.

Primary sources:

- Data Dictionary;
- saved query library;
- approved join patterns;
- module-specific query templates.

Output block:

```json
{
  "type": "sql_draft",
  "purpose": "string",
  "sql": "string",
  "parameters": [],
  "tables": [],
  "columns": [],
  "join_patterns": [],
  "assumptions": [],
  "warnings": []
}
```

Rejected requests:

- `update`;
- `delete`;
- `insert`;
- `merge`;
- DDL;
- requests without enough table/column confidence.

## Tool: Oracle Docs

Intent:

```text
oracle_docs
```

Purpose:

Find official Oracle documentation and produce a short source-bound summary.

Primary sources:

- official Oracle documentation lookup;
- local Oracle docs cache.

Output block:

```json
{
  "type": "oracle_docs",
  "title": "string",
  "url": "string",
  "summary": "string",
  "source_status": "live_official|cached_official|not_found",
  "fetched_at": "string",
  "expires_at": "string"
}
```

Rules:

- official Oracle link required for authoritative answer;
- cache timestamp required when cached;
- unavailable web returns local-limited state.

## Tool: Clarification

Intent:

```text
ambiguous
```

Purpose:

Ask one focused follow-up when the assistant cannot safely route or answer.

Output:

```json
{
  "answer_type": "clarification",
  "summary": "I need one detail before I can answer safely.",
  "choices": [
    {
      "label": "Workbench help",
      "value": "workbench_help"
    }
  ]
}
```

Clarification should be preferred over low-confidence SQL or cross-source
guessing.
