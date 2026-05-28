# Workbench Assistant Privacy And History Policy

## Purpose

The assistant can receive sensitive questions, file names, SQL snippets, and
client/domain references. This document defines a conservative privacy and
history policy for future implementation.

## Policy Summary

```text
minimize stored chat history
never store secrets
scope every persisted assistant artifact
do not leak denied source metadata
sanitize external lookups
make saved drafts explicit
```

## Conversation History

Recommended baseline:

- do not persist full conversation history by default;
- keep short-lived in-memory session state for the open panel;
- persist only explicit user-created artifacts such as saved SQL drafts;
- if history is enabled later, scope it by user, project, domain, environment,
  and visibility.

Reason:

Consultants may paste sensitive context into questions. Storing chat history by
default would create unnecessary privacy and review burden.

## Data That Must Not Be Stored

The assistant should reject or redact:

```text
passwords
API keys
OTM credentials
database credentials
tokens
private endpoint URLs
client secrets
raw production extracts
real client personal data
```

If the user pastes obvious secrets, the assistant should not repeat them back.

## Saved SQL Drafts

SQL drafts become persistent only when the user explicitly chooses to save.

Saved draft fields should include:

```text
scope
status=draft
created_by
source citations
tables and columns
warnings
created_at
```

Drafts are not approved query examples until reviewed.

## Source Search Privacy

Search behavior must follow:

```text
filter by scope first
shape results second
render snippets last
```

Denied results should not reveal:

- title;
- path;
- file name;
- client name;
- snippet;
- count of hidden records.

## External Lookup Privacy

Before calling Oracle docs or any external provider:

- remove project/client names;
- remove environment names;
- remove credentials;
- remove private URLs;
- remove raw data values;
- keep only generic Oracle/OTM technical terms.

External query text should be stored only after sanitization.

## Optional AI Privacy

If optional AI is added later:

- send only source snippets already authorized for the user;
- do not send denied/private data;
- do not send secrets;
- include a feature flag to disable AI;
- record `cost_level=ai` or `web_plus_ai`;
- preserve source citations from retrieval, not from the model.

## Logging Policy

Logs should record operational metadata, not sensitive content.

Allowed:

```text
intent
source types searched
result count after scope filtering
latency
cache hit/miss
error codes
user id or audit-safe actor id
scope ids
```

Avoid:

```text
raw user messages
full SQL text unless explicitly saved
file snippets
Oracle query before sanitization
credentials or tokens
```

## Retention Policy

Planning recommendation:

- transient panel messages: not persisted;
- saved drafts: retained until user deletes/retires;
- Oracle cache: expires by policy and can be purged;
- index records: rebuilt from source, not treated as permanent record;
- audit logs: follow existing Workbench governance.

## Future Validation

Tests should cover:

- chat message not persisted by default;
- saved SQL draft is scoped;
- denied result does not leak metadata;
- external lookup query is sanitized;
- pasted secret is redacted or rejected;
- optional AI receives only authorized snippets.
