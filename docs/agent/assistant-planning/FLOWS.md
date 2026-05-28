# Workbench Assistant Macroflows And Microflows

## User Entry Flow

```mermaid
flowchart TD
  A["Consultant is on any Workbench screen"] --> B["Lower-right robot launcher visible"]
  B --> C["Consultant clicks launcher"]
  C --> D["Assistant panel opens"]
  D --> E["Panel receives route, module, client/domain, environment, and user context"]
  E --> F["Assistant shows contextual quick actions"]
  F --> G["Consultant asks question or picks quick action"]
```

## Macroflow: Ask For Help On Current Screen

```mermaid
sequenceDiagram
  participant U as Consultant
  participant UI as Assistant Panel
  participant API as Assistant API
  participant R as Intent Router
  participant H as Help Index
  participant S as Source Layer

  U->>UI: "How do I use this screen?"
  UI->>API: message + route/module/context
  API->>R: classify intent
  R->>H: search current module help
  H->>S: attach source snippets
  S-->>API: answer blocks + citations
  API-->>UI: contextual help response
  UI-->>U: steps, source links, related actions
```

Expected answer shape:

```text
This screen is used to review rate batch issues.

Steps:
1. Check blocker summary.
2. Open the table detail if the issue references a table.
3. Fix source data or return to staging.

Sources:
- Rates Studio help index
- Current route metadata
```

## Macroflow: Find Template Or File

```mermaid
flowchart TD
  A["User asks for template/file/evidence"] --> B["Intent: find_artifact"]
  B --> C["Apply current scope guard"]
  C --> D["Search source catalog"]
  D --> E["Rank by exact terms, module, status, version, and recency"]
  E --> F{"Result allowed?"}
  F -->|yes| G["Return result cards with open/copy actions"]
  F -->|no| H["Return scoped no-access or no-results state"]
```

Result card fields:

```text
title
source_type
module
client/domain
environment
visibility
status
version/current flag
path or route target
last indexed timestamp
```

## Macroflow: Navigate To Workbench Area

```mermaid
flowchart LR
  A["User asks where to do a task"] --> B["Intent: navigate"]
  B --> C["Search route/action metadata"]
  C --> D["Check backend navigation permissions"]
  D --> E{"Allowed route?"}
  E -->|yes| F["Return route suggestion + Open action"]
  E -->|no| G["Explain unavailable route and needed permission/context"]
```

Navigation suggestions should never be hardcoded only in the frontend. They
should use backend-owned navigation and module capability metadata.

## Macroflow: SQL Helper

```mermaid
flowchart TD
  A["User asks for SQL"] --> B["Intent: sql_help"]
  B --> C["Extract candidate entities"]
  C --> D["Search Data Dictionary tables and columns"]
  D --> E["Search approved query examples"]
  E --> F{"Enough confidence?"}
  F -->|no| G["Ask focused follow-up"]
  F -->|yes| H["Assemble SQL draft from templates"]
  H --> I["Attach table/column citations"]
  I --> J["Show confidence, assumptions, and warnings"]
  J --> K["Offer copy or save as draft query"]
```

SQL generation must be template-led, not free-form:

```text
select template
  -> table/column resolution
  -> join pattern lookup
  -> user-supplied filter insertion
  -> dictionary citation
  -> saved-query comparison
  -> draft output
```

SQL response should include:

```text
purpose
query draft
tables used
columns used
join assumptions
filters requiring user input
sources
confidence
copy/save actions
```

## SQL Helper Microflow: Ambiguous Table

```mermaid
flowchart TD
  A["User asks: shipments with X"] --> B["Find table candidates"]
  B --> C{"Multiple likely tables?"}
  C -->|yes| D["Ask user to choose table family"]
  D --> E["Shipment header"]
  D --> F["Shipment stop"]
  D --> G["Shipment status/event"]
  C -->|no| H["Continue SQL draft"]
```

The assistant should prefer a short clarification over generating a confident
but wrong query.

## Macroflow: Oracle Documentation Lookup

```mermaid
sequenceDiagram
  participant U as Consultant
  participant UI as Assistant Panel
  participant API as Assistant API
  participant C as Cache
  participant W as Oracle Docs Connector
  participant S as Source Layer

  U->>UI: "What is the REST endpoint for post shipment?"
  UI->>API: message + explicit oracle_docs mode
  API->>C: check cache
  alt fresh cache exists
    C-->>API: cached official source
  else cache missing or expired
    API->>W: search official Oracle docs
    W-->>API: result links and extracted snippets
    API->>C: store cache record
  end
  API->>S: create source-bound summary
  S-->>UI: link, summary, freshness metadata
  UI-->>U: official link + short targeted summary
```

Oracle docs rules:

- Search should prefer official Oracle domains.
- Response must include a link.
- Response must distinguish official source content from Workbench inference.
- Cache must include fetch time and expiration.
- If no official source is found, the assistant should say so.

## Microflow: Permission-Denied Result

```mermaid
flowchart TD
  A["Search finds matching private artifact"] --> B["Scope guard checks user"]
  B --> C{"User can access?"}
  C -->|yes| D["Return artifact"]
  C -->|no| E["Do not expose title/path/content"]
  E --> F["Return generic scoped message"]
```

Generic response:

```text
I found matching material outside your current accessible scope. Change context
or request access if you expected to see it.
```

Do not reveal private client names, file titles, paths, or snippets through the
denied response.

## UI State Map

```mermaid
stateDiagram-v2
  [*] --> Closed
  Closed --> Opening: click launcher
  Opening --> Ready
  Ready --> Searching: submit question
  Searching --> AnswerReady
  Searching --> NeedsClarification
  Searching --> Blocked
  Searching --> OfflineLimited
  AnswerReady --> Ready: ask another question
  NeedsClarification --> Searching: answer follow-up
  Blocked --> Ready: change context or action
  OfflineLimited --> Ready: continue local-only
  Ready --> Closed: close panel
```

## Contextual Quick Actions

Quick actions should vary by current route/module:

| Context | Suggested actions |
|---|---|
| Cockpit | Help for this context, find project info, explain Public View |
| Master Data | Find template, validate dependency, build SQL from table |
| Rates | Find rate query, explain batch issue, open table detail help |
| Load Plan | Find cutover package, explain CSVUTIL sequence, find evidence |
| Integration | Explain mapping field, find payload artifact, Oracle docs lookup |
| Order Release | Find template, explain XML preview, find generated artifact |
| Assets | Find template/file, explain version/link/archive |
| Settings | Explain user/role/grant/policy, find access scope guidance |

## Response Contract

Every answer should be structured internally as:

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

The UI can render this as conversational text, but the backend should keep the
contract structured.
