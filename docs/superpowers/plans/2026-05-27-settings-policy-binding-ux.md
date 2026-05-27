# Settings Policy Binding UX Plan

## Goal

Make Settings explain where each access policy can be bound before users start
using policy IDs on operational records.

## Tasks

- [x] Define the task contract and scope guardrails.
- [x] Add backend tests for access-policy binding guidance.
- [x] Add backend-owned binding guidance fields to access-policy serialization.
- [x] Update frontend platform types.
- [x] Render Settings policy-binding review in the setup surface.
- [x] Update the Settings route test for the new review.
- [x] Run backend/frontend validation.
- [x] Capture browser QA evidence.
- [x] Update validation and handoff docs.

## Validation Commands

```powershell
pytest tests/test_operational_context.py -q
npm test -- src/app/App.test.tsx -t "Settings"
npm run build
git diff --check
```
