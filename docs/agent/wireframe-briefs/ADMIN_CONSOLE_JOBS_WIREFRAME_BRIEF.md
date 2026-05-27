# Michelangelo Wireframe Brief - Admin Console / Jobs

**Status:** ready for Figma wireframe pass after user scope approval
**Date:** 2026-05-26
**Source scope review:** `docs/agent/module-scope/ADMIN_CONSOLE_JOBS_SCOPE_REVIEW.md`

## 1. Review Context

Screen/flow type:
Restricted platform administration, jobs, audit, and connection management.

Primary user task:
Administer users, roles, setup, feature flags, jobs, audit, and OTM connection
metadata without exposing sensitive controls to normal users.

User profile:
ADMIN, MASTER, authorized technical lead.

Task criticality:
High. Admin mistakes can expose tools, credentials, or unsafe capabilities.

Input reviewed:
Admin Console consolidated spec and scope review.

Evidence source:
Repository documentation only. No live UI reviewed.

Assumptions:
Backend owns capabilities, route visibility, feature flags, jobs, audit, and
secret masking.

## 2. Archetypes

- settings/admin;
- job console;
- audit search;
- critical configuration;
- user/role management.

## 3. Route Inventory For Wireframes

```text
/admin
/admin/setup
/admin/users
/admin/feature-flags
/admin/jobs
/admin/jobs/:jobId
/admin/audit
/admin/otm-connections
```

## 4. UX Findings To Design Around

ID:
ADM-UX-01

Severity:
P1 High

Category:
Safety and permissioning

Where:
Admin hub and route visibility.

Evidence:
Admin Console must not appear for normal users and must not leak sensitive
configuration.

Problem:
Admin controls mixed into consultant flows make capabilities and sensitive
actions discoverable in the wrong context.

User impact:
Security risk and workflow confusion.

Recommendation:
Wireframe unauthorized/disabled states and keep admin routes separate from
Project Cockpit and modules.

Acceptance criteria:
Normal users see no admin controls, or only a clear permission-blocked state.

---

ID:
ADM-UX-02

Severity:
P2 Medium

Category:
Feedback and recovery

Where:
Jobs and job detail.

Evidence:
Jobs must show status, failures, and source context without becoming an unsafe
technical console.

Problem:
Job rows without clear source/action/recovery make failures hard to resolve.

User impact:
Admins cannot tell whether to retry, inspect source module, or escalate.

Recommendation:
Wireframe job detail with status timeline, source object, safe result summary,
error category, and next action.

Acceptance criteria:
Failed jobs show source, reason, and safe next action.

## 5. Required Wireframe States

- unauthorized user;
- setup incomplete;
- users list empty;
- role mutation blocked;
- feature flag change confirmation;
- job running;
- job failed;
- audit no results;
- connection missing;
- credential masked.

## 6. Wireframe Acceptance Criteria

- Admin routes are permission-gated.
- Sensitive values are masked.
- Feature flag changes show impact.
- Jobs show source, status, result, and recovery.
- Audit search is client-safe.

## 7. External Validation Recommended

After Figma:

- Michelangelo review for admin safety;
- security review for sensitive states;
- browser QA plan for unauthorized access and job failure.
