# Settings Setup Recovery UX Plan

## Goal

Make Settings usable when setup data is missing or scoped selectors are empty.

## Tasks

- [x] Define task contract and scope guardrails.
- [x] Add failing frontend assertion for setup recovery and empty selector states.
- [x] Render setup recovery with backend blockers/actions and Return to Cockpit.
- [x] Render compact empty/blocked text beside setup selectors.
- [x] Run frontend validation and build.
- [x] Capture browser QA evidence.
- [x] Update validation and handoff docs.

## Validation Commands

```powershell
npm test -- src/app/App.test.tsx -t "Settings"
npm run build
git diff --check
```
