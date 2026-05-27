# Michelangelo Wireframe Brief - Evidence Hub

**Status:** ready for Figma wireframe pass after user scope approval
**Date:** 2026-05-26
**Source scope review:** `docs/agent/module-scope/EVIDENCE_HUB_SCOPE_REVIEW.md`

## 1. Review Context

Screen/flow type:
Evidence, artifact, archive, and audit traceability surface.

Primary user task:
Find client-safe evidence, inspect its source, review/download allowed
artifacts, and build archive packages.

User profile:
Functional lead, project lead, auditor/sponsor, consultant.

Task criticality:
High. Evidence must be trusted and safe to share.

Input reviewed:
Evidence Hub consolidated spec and scope review.

Evidence source:
Repository documentation only. No live UI reviewed.

Assumptions:
Backend owns evidence safety, artifact download readiness, hash verification,
sensitivity, and audit.

## 2. Archetypes

- artifact/library manager;
- audit/report dashboard;
- guarded download flow;
- archive builder;
- source timeline.

## 3. Route Inventory For Wireframes

```text
/evidence
/evidence/:evidenceId
/evidence/:evidenceId/download/:artifactId
/evidence/archive/new
/evidence/archive
/evidence/archive/:archiveId
/evidence/source/:sourceType/:sourceId
/evidence/artifacts/:artifactId
/evidence/audit
```

## 4. UX Findings To Design Around

ID:
EVD-UX-01

Severity:
P1 High

Category:
Trust and safety

Where:
Evidence detail and artifact download.

Evidence:
Evidence Hub must not expose raw payloads, local paths, or unsafe artifact
content.

Problem:
A file-browser UI could make unsafe details feel normal.

User impact:
Sensitive data leakage and loss of client trust.

Recommendation:
Wireframe evidence detail as a client-safe summary with source, status,
artifact references, sensitivity, and guarded download review.

Acceptance criteria:
No route shows raw payloads, local paths, or download actions without readiness.

---

ID:
EVD-UX-02

Severity:
P2 Medium

Category:
Information architecture

Where:
Archive builder and archive library.

Evidence:
Archive packages should be based on filtered client-safe evidence, not ad hoc
file selection.

Problem:
Users may not know which evidence is eligible for an archive.

User impact:
Incomplete or unsafe handoff packages.

Recommendation:
Wireframe archive builder with filters, eligibility summary, excluded reasons,
and preview before creation.

Acceptance criteria:
Archive creation shows what will be included and why anything is excluded.

## 5. Required Wireframe States

- no evidence;
- filtered no results;
- evidence with no artifact;
- sensitive artifact;
- download blocked;
- hash verification failed;
- archive ineligible;
- archive preview ready;
- archive created.

## 6. Wireframe Acceptance Criteria

- Evidence remains client-safe.
- Downloads are guarded and auditable.
- Archive builder shows eligibility and preview.
- Source timeline links back to owning module without rebuilding its workflow.
- Artifact detail never exposes local filesystem paths.

## 7. External Validation Recommended

After Figma:

- Michelangelo review for trust/safety;
- security review of evidence/download states;
- browser QA plan for blocked download and archive flow.
