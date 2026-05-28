# Settings Role And Grant Review UX Plan

## Goal

Make role/grant scope review clear in Settings before continuing to the next
module.

## Tasks

- [x] Define task contract and scope guardrails.
- [x] Add failing backend assertion for grant binding guidance.
- [x] Add failing frontend assertion for grant-binding review.
- [x] Implement backend-owned grant guidance fields.
- [x] Update frontend platform types.
- [x] Render grant-binding review.
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
