# GUI Project Cockpit Summary Contract

**Status:** backend contract delivered  
**Branch:** `codex/project-cockpit-summary`  
**Endpoint:** `GET /api/v1/platform/project-cockpit/summary`

## Objective

Provide the first GUI-ready Project Cockpit read model without moving business
rules into the frontend.

The response is designed for the workbench home screen and should let the GUI
render:

- active project/profile/environment/domain context;
- project setup readiness;
- visible module summary;
- recent jobs;
- recent artifacts;
- recent client-safe evidence;
- global cockpit actions.

## Response Shape

```json
{
  "module_id": "home",
  "title": "Project Cockpit",
  "status": "ready",
  "description": "Project-level operational overview for the active OTM workbench context.",
  "active_context": {},
  "setup_status": {},
  "counts": {
    "recent_jobs": 1,
    "recent_artifacts": 1,
    "recent_evidence": 1
  },
  "module_summary": {
    "total": 1,
    "counts_by_status": {},
    "items": []
  },
  "recent_jobs": [],
  "recent_artifacts": [],
  "recent_evidence": [],
  "available_actions": []
}
```

## Safety Rules

- `recent_jobs` exposes `input_present` and `result_present`, not raw `input`
  or `result` payloads.
- `recent_artifacts` does not expose `file_path`.
- `recent_evidence.summary` uses an allowlist of GUI-safe summary keys.
- The cockpit summary is project-filtered when an active project exists.
- No real client names, values, paths, or payloads are required by this
  contract.

## GUI Usage

The frontend should treat this endpoint as the source of truth for the cockpit
overview state. It should not infer project readiness, module visibility, or
evidence safety from local rules.

Recommended first screen composition:

- top context block from `active_context`;
- setup banner from `setup_status`;
- module readiness list from `module_summary`;
- activity panels from `recent_jobs`, `recent_artifacts`, and
  `recent_evidence`;
- command buttons from `available_actions`.
