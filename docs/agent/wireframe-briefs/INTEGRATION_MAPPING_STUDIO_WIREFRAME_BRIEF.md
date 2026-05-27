# Michelangelo Wireframe Brief - Integration Mapping Studio

**Status:** ready for Figma wireframe pass after user scope approval
**Date:** 2026-05-26
**Source scope review:** `docs/agent/module-scope/INTEGRATION_MAPPING_STUDIO_SCOPE_REVIEW.md`

## 1. Review Context

Screen/flow type:
Integration definition, schema, mapping, rule, preview, and spec workspace.

Primary user task:
Create or inspect an integration definition, map source to target payloads,
resolve blockers, preview output, and generate a spec/artifacts.

User profile:
Technical-functional consultant, integration lead, implementation engineer.

Task criticality:
High. Invalid mappings or hidden blockers can produce unusable integration
artifacts.

Input reviewed:
Integration Mapping consolidated spec and scope review.

Evidence source:
Repository documentation only. No live UI reviewed.

Assumptions:
Backend owns schemas, suggestions, validation, preview, spec generation, and
artifacts.

## 2. Archetypes

- mapping/transform builder;
- workflow/detail;
- schema/path browser;
- validation review;
- artifact/spec generation.

## 3. Route Inventory For Wireframes

```text
/integration-mapping
/integration-mapping/definitions/new
/integration-mapping/definitions/:definitionId
/integration-mapping/definitions/:definitionId/systems
/integration-mapping/definitions/:definitionId/schemas
/integration-mapping/definitions/:definitionId/mapping
/integration-mapping/definitions/:definitionId/rules/:ruleId
/integration-mapping/definitions/:definitionId/rules
/integration-mapping/definitions/:definitionId/review
/integration-mapping/definitions/:definitionId/preview
/integration-mapping/definitions/:definitionId/spec
/integration-mapping/definitions/:definitionId/artifacts
/integration-mapping/systems
```

## 4. UX Findings To Design Around

ID:
IM-UX-01

Severity:
P1 High

Category:
Workflow sequencing and validation

Where:
Mapping workspace and review.

Evidence:
The spec identifies alias/path blockers, required target checklists, backend
suggestions, preview blockers, and generated artifacts.

Problem:
If mapping, rules, preview, and spec generation sit in one workspace, users may
miss unresolved blockers.

User impact:
Invalid previews or specs that appear trustworthy.

Recommendation:
Wireframe a route-level flow from mapping to rules to review to preview/spec,
with blocker summaries carried forward.

Acceptance criteria:
Preview and spec routes visibly depend on passing backend validation.

---

ID:
IM-UX-02

Severity:
P2 Medium

Category:
Information architecture and cognitive load

Where:
Mapping workspace.

Evidence:
Integration mappings include joins, loops, lookups, aliases, source/target
paths, and backend suggestions.

Problem:
A raw field-to-field grid cannot explain provenance, alias scope, and grouped
rules.

User impact:
Users may create rules without understanding their scope.

Recommendation:
Use grouped mapping panels, selected rule detail, backend suggestion reasons,
and provenance chips.

Acceptance criteria:
Users can tell why a mapping was suggested and which alias/path scope it uses.

## 5. Required Wireframe States

- no definitions;
- create definition missing schema root;
- schemas unavailable;
- backend suggestions unavailable;
- required target missing;
- invalid alias/path;
- preview blocked;
- preview generated;
- spec generated;
- artifact ready.

## 6. Wireframe Acceptance Criteria

- Definition is the primary object.
- Mapping, rule detail, review, preview, and spec are separated.
- Backend suggestion confidence/reasons are visible.
- Alias/path blockers are actionable.
- Raw payloads and real client data are not shown.

## 7. External Validation Recommended

After Figma:

- Michelangelo review for mapping comprehension;
- Catalog schema path guidance review;
- browser QA plan for invalid alias/path recovery.
