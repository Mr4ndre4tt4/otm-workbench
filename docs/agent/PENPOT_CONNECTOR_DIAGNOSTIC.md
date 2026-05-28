# Penpot Connector Diagnostic

**Status:** active
**Date:** 2026-05-26

## Summary

The Penpot project is reachable and connected to the correct file. The standard
Codex-exposed `mcp__penpot__` tool wrapper is failing in this conversation with
a transport deserialization error, but the underlying Penpot MCP endpoint works
through direct JSON-RPC over the configured stream endpoint.

## Target Confirmed

Connected file:

```text
otm-workbech-new-wireframe
```

Connected identifiers:

```text
file-id: e7a86fff-661d-81c1-8008-14af24af603d
page-id: e7a86fff-661d-81c1-8008-14af24af603e
initial page name: 01 Shell, Login, Logout, and Project Cockpit
```

Initial page state:

```text
root child count: 0
```

## Failure Observed

Standard tool calls failed:

```text
mcp__penpot__.high_level_overview
mcp__penpot__.execute_code
```

Both returned:

```text
Transport send error ... Deserialize error: data did not match any variant of
untagged enum JsonRpcMessage
```

## Endpoint Validation

Manual JSON-RPC initialization against the configured Penpot MCP stream endpoint
returned:

```text
status: 200
content-type: text/event-stream
serverInfo.name: penpot
serverInfo.version: 1.0.0
protocolVersion: 2024-11-05
```

Manual `tools/list` returned the Penpot tool catalog.

Manual `tools/call` for `high_level_overview` returned the expected Penpot
overview text.

Manual `tools/call` for `execute_code` returned the current Penpot file/page
state.

## Reversible Write Smoke Test

Manual `execute_code` created and removed one temporary board in the same call:

```text
before: 0
afterCreate: 1
afterRemove: 0
cleaned: true
```

No persistent Penpot object was left by the smoke test.

## Working Hypothesis

The issue is not the Penpot token, not the target file, and not Penpot
availability. The failure is localized to the Codex tool wrapper or current
streamable HTTP adapter state for this conversation.

## Temporary Operating Decision

Until the normal `mcp__penpot__` wrapper recovers, Penpot work may proceed by
calling the configured Penpot MCP stream endpoint directly through JSON-RPC from
PowerShell, while keeping these controls:

- never print or store the Penpot user token;
- initialize a fresh MCP session per operation batch;
- use the returned MCP session id for subsequent calls;
- create or update only the approved target file/page;
- run readback checks after writes;
- export or inspect representative shapes when practical;
- document every Penpot page/board created.

## Next Step

Use the validated JSON-RPC path for remaining approved Penpot modules until the
standard wrapper recovers. For each module, confirm the target file/page before
writing and read back board names, counts, routes, states, and marker metadata.
