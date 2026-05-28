# Michelangelo Wireframe Brief - Developer Tools

**Status:** ready for Figma wireframe pass after user scope approval
**Date:** 2026-05-26
**Source scope review:** `docs/agent/module-scope/DEVELOPER_TOOLS_SCOPE_REVIEW.md`

## 1. Review Context

Screen/flow type:
Restricted technical diagnostics hub and read-mostly inspection tools.

Primary user task:
Inspect Data Dictionary, FK Catalog, schema packs, and environment readiness
when authorized, without exposing unsafe technical details.

User profile:
DBA, MASTER, developer, authorized technical consultant.

Task criticality:
Medium to high. Diagnostics must support troubleshooting without leaking paths,
payloads, or credentials.

Input reviewed:
Developer Tools consolidated spec and scope review.

Evidence source:
Repository documentation only. No live UI reviewed.

Assumptions:
Backend owns feature flags, capabilities, disabled reasons, diagnostics, and
safe metadata.

## 2. Archetypes

- diagnostic console;
- technical metadata explorer;
- readiness report;
- guarded admin-like utility.

## 3. Route Inventory For Wireframes

```text
/dev-tools
/dev-tools/data-dictionary
/dev-tools/data-dictionary/:tableName
/dev-tools/fk-catalog
/dev-tools/schema-packs
/dev-tools/environment-readiness
/dev-tools/runs/:runId
```

## 4. UX Findings To Design Around

ID:
DEV-UX-01

Severity:
P1 High

Category:
Permissioning and trust

Where:
Developer Tools hub.

Evidence:
Developer Tools must be hidden from USER and optional for normal delivery.

Problem:
If diagnostics look like normal product modules, consultants may rely on
technical tools instead of governed workflows.

User impact:
Confusion, support risk, and unsafe exposure.

Recommendation:
Wireframe a guarded technical hub with clear role/capability status and
disabled reasons.

Acceptance criteria:
The UI clearly communicates that these tools are restricted diagnostics.

---

ID:
DEV-UX-02

Severity:
P1 High

Category:
Data safety

Where:
Schema packs, environment readiness, Data Dictionary detail.

Evidence:
The spec forbids local paths, credentials, endpoints, and raw unsafe payloads.

Problem:
Diagnostics often tempt raw logs and local path display.

User impact:
Sensitive data leakage.

Recommendation:
Use safe summaries and redacted metadata only.

Acceptance criteria:
No wireframe contains local paths, credentials, endpoints, or raw payloads.

## 5. Required Wireframe States

- unauthorized user;
- feature disabled;
- active context missing;
- Data Dictionary unavailable;
- table detail loaded;
- no FK relationships;
- schema pack failed;
- environment readiness blocked;
- diagnostic run failed.

## 6. Wireframe Acceptance Criteria

- Developer Tools are visibly restricted.
- Diagnostics are read-mostly unless a governed action exists.
- No local paths or secrets appear.
- Catalog duplication is intentional and role-distinguished.
- Disabled reasons come from backend.

## 7. External Validation Recommended

After Figma:

- Michelangelo review for technical clutter and safety;
- security review for redaction;
- browser QA plan for unauthorized and disabled states.
