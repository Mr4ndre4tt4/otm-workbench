# GUI Rates Action Execution

**Status:** implemented
**Branch:** `codex/gui-rates-action-execution`

## Objective

Make backend-owned Rates actions executable from the GUI without moving action
rules into the frontend.

## Contract

Rates batch detail returns `available_actions`. The frontend executes supported
actions by calling the action `href` with the action `method`.

Current GUI support:

```text
method: POST
result_hint: refresh_object | refresh_list
```

After a successful action, the GUI invalidates Rates summary and selected batch
detail queries so the backend remains the source of truth.

## GUI Behavior

The selected batch detail panel now:

- renders backend action labels;
- respects backend `disabled` state;
- executes enabled `POST` actions through the action `href`;
- shows a lightweight success or error message;
- refreshes the Rates object/list when requested by `result_hint`.

## Guardrails

The frontend still does not infer:

- approval readiness;
- validation readiness;
- export readiness;
- permissions;
- disabled reasons.

Those remain backend-owned through the action contract.

## Validation

- `frontend/src/app/App.test.tsx` verifies action execution calls the backend
  action `href` and shows success.
- Backend validation and action contracts remain covered by Rates tests.
