# GUI Evidence Hub Functional Workflow Plan

**Linear:** OTM-94
**Spec:** `docs/superpowers/specs/2026-05-22-gui-evidence-hub-functional-workflow-design.md`

## Steps

1. Add typed frontend contracts for Evidence Hub filters, archive packages, and
   guarded artifact downloads.
2. Refactor `/evidence` into one coherent search/detail workflow:
   `Find -> Inspect -> Download -> Archive`.
3. Add filter controls for source module, evidence type, status, project,
   sensitivity, artifact, and manifest.
4. Add backend-backed archive creation and artifact download actions in the
   selected-object panel.
5. Add functional Vitest coverage for filtering, detail fetch, download,
   archive creation, bearer auth, and route return-state.
6. Update GUI docs/roadmap/QA matrix and Linear with validation evidence.

## Verification

```text
npm run test -- AppFunctionalEvidenceHub.test.tsx
npm run lint
npm run build
python -m pytest tests/test_evidence_hub_index.py -q
git diff --check
```
