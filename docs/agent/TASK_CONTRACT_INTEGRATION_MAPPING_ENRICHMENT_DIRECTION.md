# Task Contract: Integration Mapping Enrichment Direction

**Date:** 2026-05-28
**Status:** active direction consolidation
**Owner:** Codex / user review

## Objective

Incorporate the user-provided Integration Mapping prototype prompts and
architecture document into the project direction without copying prototype-only
assumptions into the implementation baseline.

## In Scope

- Enrich the consolidated Integration Mapping spec with the `Integration Spec
  Compiler` direction.
- Add `Enrichment Pipeline` as a first-class To-Be route and backend-owned
  domain concern.
- Preserve existing project governance:
  - backend-owned contracts and readiness;
  - explicit client/domain/environment scope;
  - no real client data in docs, fixtures, screenshots, tests, or seeds;
  - generated artifacts through guarded backend downloads.
- Record Figma/GitHub follow-up expectations for the dedicated Integration
  Mapping delivery slice.

## Out of Scope

- No backend implementation in this task.
- No frontend route implementation in this task.
- No production-like client identifiers, real endpoints, CNPJ/CPF, payload
  values, credentials, or local paths are to be carried into official docs.
- No GitHub issue mutation unless explicitly confirmed after the direction is
  reviewed.

## Source Inputs

- `C:/Users/Enzo Trabalho/Downloads/files.zip`
- `C:/Users/Enzo Trabalho/Downloads/integration-mapping-studio-architecture.docx`
- `C:/Users/Enzo Trabalho/Downloads/otm-workbench-integration-mapping.zip`
- Draft intake brief:
  `outputs/integration-mapping-direction-intake/direction-brief.md`

## Acceptance Criteria

- The consolidated spec names the new direction and the adaptation boundaries.
- The IA includes `/integration-mapping/definitions/:definitionId/enrichment`.
- Backend contract gaps include enrichment steps, substeps, enriched fields,
  readiness, validation, preview provenance, and generated spec integration.
- QA journeys and implementation slices include enrichment.
- Handoff records the docs/design/tracking status and next steps.

## Risks

- Prototype data may contain real client/environment details and must remain
  sanitized in official docs.
- Enrichment may be incorrectly folded into generic lookups, losing execution
  order, substeps, loop scope, and output field provenance.
- A frontend-only implementation would violate the module's backend-first
  architecture.
