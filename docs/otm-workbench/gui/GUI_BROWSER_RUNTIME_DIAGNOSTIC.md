# GUI Browser Runtime Diagnostic

**Status:** workaround available
**Date:** 2026-05-21
**Branch:** `codex/browser-runtime-diagnostic`
**Scope:** Browser plugin failure and local Chrome fallback.

## 1. Problem

The in-app Browser plugin could not open GUI routes because its required
Node-backed runtime failed before a browser tab was created.

The failure is not caused by the OTM Workbench frontend route. The local Vite
route responded successfully.

## 2. Root Cause Evidence

The Browser plugin depends on the `node_repl` runtime. A minimal runtime check
failed before importing browser code:

```text
nodeRepl.write(JSON.stringify({ ok: true }))
```

Observed failure:

```text
windows sandbox failed: CreateProcessWithLogonW failed: 1326
```

After terminating the stale `node_repl` process, the MCP transport remained
closed in the current session:

```text
Transport closed
```

This means the in-app Browser plugin cannot recover inside the same Codex
session. Restarting the Codex session/plugin host is the likely recovery path
for the plugin runtime itself.

## 3. Route Health

The frontend route was verified independently:

```text
npm run dev -- --host 127.0.0.1 --port 8032
```

Readiness check:

```text
http://127.0.0.1:8032/__gui/component-gallery
200
```

## 4. Working Fallback

Chrome is installed at:

```text
C:\Program Files\Google\Chrome\Application\chrome.exe
```

The route can be opened in external Chrome with:

```text
Start-Process -FilePath "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList @("http://127.0.0.1:8032/__gui/component-gallery")
```

This opened a visible Chrome window titled:

```text
OTM Workbench - Google Chrome
```

## 5. Current Guidance

Use external Chrome for manual visual inspection while the in-app Browser
plugin runtime is unavailable.

Do not claim Browser-plugin screenshot or pixel evidence until `node_repl` can
successfully execute a minimal JavaScript cell and the Browser bootstrap can
create or select an `iab` tab.

## 6. Recovery Checklist

When attempting to restore Browser plugin support:

```text
1. Restart the Codex desktop session or plugin host.
2. Run a minimal node_repl check.
3. If node_repl works, run Browser bootstrap.
4. Open http://127.0.0.1:8032/__gui/component-gallery through the Browser plugin.
5. Capture screenshot evidence only after the Browser plugin succeeds.
```

Until then, keep GUI validation split into:

```text
- automated frontend checks
- external Chrome manual inspection
- explicit note that Browser plugin evidence is unavailable
```
