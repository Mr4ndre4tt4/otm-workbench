# Workbench Assistant Response Contract

## Purpose

This document defines the future structured response shape for the Workbench
Assistant. The UI may render responses conversationally, but the backend should
return typed blocks so safety, citations, testing, and rendering remain
deterministic.

## Top-Level Response

```json
{
  "response_id": "asst_resp_001",
  "answer_type": "help",
  "summary": "Short source-bound answer.",
  "blocks": [],
  "actions": [],
  "sources": [],
  "confidence": "high",
  "source_mode": "indexed",
  "cost_level": "local",
  "scope": {
    "project_id": "proj_demo",
    "profile_id": "profile_demo",
    "domain_name": "OTM1",
    "environment_name": "UAT",
    "visibility": "PRIVATE"
  },
  "warnings": [],
  "requires_follow_up": false
}
```

## Answer Types

| Type | Meaning |
|---|---|
| `help` | Workbench usage answer |
| `search_results` | Finder result cards |
| `navigation` | Route/action recommendation |
| `sql_draft` | Draft SQL or SQL explanation |
| `oracle_docs` | Official Oracle docs result |
| `clarification` | One follow-up question |
| `blocked` | Permission, missing source, or safety block |
| `offline_limited` | Web-dependent tool unavailable |
| `error` | Unexpected failure with safe message |

## Confidence

| Value | Meaning |
|---|---|
| `high` | Direct source match, validated source, or approved query pattern |
| `medium` | Source-backed but requires assumptions |
| `low` | Insufficient for final answer; usually asks clarification |

## Source Mode

| Value | Meaning |
|---|---|
| `indexed` | From local indexed sources |
| `cached` | From local cache |
| `live_official` | From live official Oracle lookup |
| `generated_draft` | Generated from templates and cited sources |
| `none` | No source found, used for blocked/clarification/error |

## Cost Level

| Value | Meaning |
|---|---|
| `local` | Local search/rules/templates only |
| `web` | Live web/API lookup |
| `ai` | Optional AI call only |
| `web_plus_ai` | Web/API plus optional AI |

## Source Object

```json
{
  "source_id": "src_001",
  "source_type": "data_dictionary",
  "title": "SHIPMENT table",
  "path_or_url": null,
  "module_id": "catalog",
  "source_mode": "indexed",
  "confidence": "high",
  "indexed_at": "2026-05-28T10:00:00Z",
  "fetched_at": null,
  "expires_at": null,
  "scope": {
    "domain_name": "PUBLIC",
    "environment_name": null,
    "visibility": "PUBLIC"
  }
}
```

## Action Object

```json
{
  "action_id": "open_rates_batch_library",
  "label": "Open batch library",
  "kind": "route",
  "target": "/rates/batches",
  "enabled": true,
  "disabled_reason": null
}
```

Action kinds:

| Kind | Meaning |
|---|---|
| `route` | Navigate inside Workbench |
| `copy` | Copy text to clipboard |
| `save_draft` | Save a draft query or assistant artifact |
| `refresh` | Refresh cached Oracle docs |
| `reindex` | Request authorized source reindex |

## Block Types

### Steps Block

```json
{
  "type": "steps",
  "title": "How to use this screen",
  "items": [
    "Review the blocker summary.",
    "Open the table detail for row-level issues."
  ]
}
```

### Result Cards Block

```json
{
  "type": "result_cards",
  "items": [
    {
      "title": "Location master data template",
      "subtitle": "Master Data template",
      "source_type": "asset",
      "status": "validated",
      "version_label": "v4",
      "actions": []
    }
  ]
}
```

### SQL Draft Block

```json
{
  "type": "sql_draft",
  "purpose": "Find shipment by GID",
  "sql": "select s.shipment_gid from shipment s where s.shipment_gid = :shipment_gid",
  "parameters": [
    {
      "name": "shipment_gid",
      "description": "Shipment GID to search for"
    }
  ],
  "tables": ["SHIPMENT"],
  "columns": ["SHIPMENT.SHIPMENT_GID"],
  "assumptions": [],
  "warnings": []
}
```

### Oracle Docs Block

```json
{
  "type": "oracle_docs",
  "title": "Oracle documentation result title",
  "url": "https://docs.oracle.com/...",
  "summary": "Short targeted summary.",
  "source_status": "live_official",
  "fetched_at": "2026-05-28T10:00:00Z",
  "expires_at": "2026-06-04T10:00:00Z"
}
```

### Clarification Block

```json
{
  "type": "clarification",
  "question": "Which shipment area do you want to query?",
  "choices": [
    {
      "label": "Shipment header",
      "value": "shipment_header"
    },
    {
      "label": "Shipment stops",
      "value": "shipment_stops"
    }
  ]
}
```

## Rendering Rules

- Always show source/cost mode when the answer is not purely local.
- SQL blocks should render in monospace with copy action.
- Blocked responses should not show suppressed result metadata.
- Oracle docs results should make the official URL visually obvious.
- Warnings should appear near the block they affect, not only at the bottom.

## Testing Rule

Frontend tests should assert block types and accessible labels, not exact prose.
Backend tests should assert sources, scope, confidence, and blocked behavior.
