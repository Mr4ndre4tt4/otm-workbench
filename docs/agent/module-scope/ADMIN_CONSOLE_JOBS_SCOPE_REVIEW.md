# Admin Console / Jobs Scope Review

**Status:** validated for wireframe brief, pending user approval before cleanup
or implementation
**Date:** 2026-05-26
**Primary spec:** `docs/otm-workbench/gui/GUI_ADMIN_CONSOLE_CONSOLIDATED_SPEC.md`

## 1. Original Intent

Admin Console should concentrate restricted platform administration without
polluting consultant workflows. It owns setup, users, roles, capabilities,
feature flags, jobs, audit, OTM connections, and module governance.

## 2. Current Evidence

The active redesign spec defines route-level admin surfaces: `/admin`,
`/admin/setup`, `/admin/users`, `/admin/feature-flags`, `/admin/jobs`,
`/admin/jobs/:jobId`, `/admin/audit`, and `/admin/otm-connections`.

## 3. Validated Target Scope

Admin Console should be treated as a restricted platform operations module:

- admin hub;
- setup and context administration;
- users and roles/capabilities;
- feature flags;
- jobs list/detail;
- audit search;
- OTM connections with secrets masked;
- module governance.

## 4. Explicit Non-Scope

- Do not expose Admin Console to normal users.
- Do not mix admin setup into Project Cockpit or module flows.
- Do not show raw credentials, tokens, or connection secrets.
- Do not make jobs a generic technical console without user-safe summaries.

## 5. Cleanup Watchlist

- Setup, jobs, audit, and flags stacked on one page.
- Sensitive configuration in normal screens.
- Feature flags without impact copy.
- Job detail without status/progress/error recovery.

## 6. Backend Contract Dependencies

- setup state and active context controls;
- users, roles, and capabilities;
- feature flag list/update;
- job list/detail/status/result;
- audit log search;
- OTM connection metadata with secret masking;
- capability checks for all admin routes.

## 7. Wireframe Inputs

Required route frames:

- admin hub;
- setup;
- users/roles;
- feature flags;
- jobs;
- job detail;
- audit;
- OTM connections.

Required states:

- unauthorized user;
- setup incomplete;
- user/role mutation blocked;
- flag change requires confirmation;
- job running;
- job failed;
- audit no results;
- connection missing or secret masked.

## 8. Open Decisions

- Whether module governance is a separate route in the first redesign.
- Which OTM connection setup actions are allowed before direct OTM submit
  exists.
- How job details should link back to source module objects.

## 9. Acceptance For Wireframe Phase

Admin can move to Penpot when route-level restricted administration and safe
jobs/audit/connection handling are accepted.
