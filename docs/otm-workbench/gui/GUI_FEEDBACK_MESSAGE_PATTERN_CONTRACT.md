# GUI Feedback Message Pattern Contract

**Status:** delivered  
**Branch:** `codex/gui-feedback-message-contract`  
**Scope:** shared inline success and error feedback for shell and module actions.

## 1. Purpose

`FeedbackMessage` is the shared inline message pattern for short user feedback
inside forms, selected object panels, and module action areas.

It centralizes `form-success` and `form-error` rendering so screens do not
invent one-off paragraph classes for backend action results.

## 2. Ownership Boundary

`FeedbackMessage` owns:

```text
- success feedback class mapping
- error feedback class mapping
- inline message element shape
```

Callers own:

```text
- deciding when a backend action produced a message
- deciding whether the message is success or error
- message text returned or derived from backend action outcomes
```

## 3. Backend Ownership

The component does not decide validation, permissions, action availability, or
business outcomes. It only renders a frontend message after backend-owned
contracts or platform hooks return a result.

## 4. Required Behavior

```text
1. Use FeedbackMessage for inline success or error text in app and module code.
2. Keep raw form-success and form-error classes inside ui/components.tsx.
3. Do not use FeedbackMessage for persistent lifecycle/readiness state; use
   StatePanel, StatusChip, ReadinessPanel, or module contracts instead.
```

## 5. Guardrails

```text
frontend/src/ui/components.test.tsx
frontend/tests/feedbackMessagePatternContract.test.ts
```

The tests verify the rendered classes and prevent raw feedback classes from
drifting into shell or module views.
