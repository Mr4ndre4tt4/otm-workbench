# Rates Route Recovery UX Plan

## Goal

Give Rates Studio a visible lifecycle map and recovery paths while preserving
the current working backend action contracts.

## Tasks

- [x] Define task contract and scope guardrails.
- [x] Add failing frontend assertion for Rates lifecycle/recovery links.
- [x] Render Rates lifecycle destination panel.
- [x] Keep selected-batch lifecycle links deterministic.
- [x] Run functional Rates test and build.
- [x] Capture browser QA evidence.
- [x] Update validation and handoff docs.

## Validation Commands

```powershell
npm test -- src/app/AppFunctionalRates.test.tsx
npm run build
git diff --check
```
