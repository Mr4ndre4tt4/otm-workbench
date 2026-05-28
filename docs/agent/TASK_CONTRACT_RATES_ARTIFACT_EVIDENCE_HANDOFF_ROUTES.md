# Task Contract: Rates Artifact, Evidence, and Load Plan Handoff Routes

## Objective

Complete the remaining Rates batch lifecycle destinations as route-level screens:
`/rates/batches/:batchId/artifacts`, `/rates/batches/:batchId/evidence`, and
`/rates/batches/:batchId/load-plan`.

## In Scope

- Keep the existing summary page links and make each destination render a
  distinct route-level workspace with `Back to Rates`.
- Reuse backend-owned artifact, evidence, batch detail, status, domain, and
  catalog load plan data.
- Allow artifact download from the route-level artifacts screen.
- Allow Load Plan package registration through the existing
  `/api/v1/modules/load-plan/packages/from-rates/:batchId` backend endpoint.
- Add focused frontend tests for direct-route recovery and handoff behavior.

## Out of Scope

- New backend persistence behavior beyond calling the existing Load Plan
  package registration endpoint.
- New Load Plan package detail UI.
- New module navigation structure or sidebar changes.

## Acceptance Criteria

- Direct navigation to artifacts, evidence, and load-plan routes renders the
  expected route title, selected batch context, and operational records.
- Each route has visible return/navigation actions.
- Artifact download still uses the backend download endpoint.
- Load Plan handoff posts to the existing package intake endpoint and shows the
  returned package identifier/status.
- `npm test -- src/app/AppFunctionalRates.test.tsx` passes.
- `npm run build` passes.
- Browser QA screenshot is captured for the route-level handoff flow.

## Validation Notes

- All fixture data remains synthetic.
- The route surfaces preserve explicit domain/environment-ready context exposed
  by the backend batch detail and generated package payload.
