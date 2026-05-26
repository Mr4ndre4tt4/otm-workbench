# GUI Admin Console Consolidated Specification

**Status:** active redesign specification  
**Date:** 2026-05-26  
**Scope:** consolidated Admin Console objective, current UI review, route-level
redesign, backend contract rules, and QA acceptance criteria.

## 1. Objective

Admin Console exists to centralize platform configuration, governance, and
administration without polluting consultant workflows.

It should answer:

```text
- Who can access what?
- Which project, profile, environment, and domain context is configured?
- Which modules and technical surfaces are enabled by feature flag?
- Which jobs are running, failed, or blocked?
- Which critical changes were made and audited?
- Why is a platform or module action unavailable?
```

Admin Console is not a business module. It must not become the place where
users operate Rates, Master Data, Load Plan, Assets, Evidence, Order Release,
or Integration Mapping.

## 2. Original Functional Scope

Foundation docs describe the Admin Console as the place for:

```text
- Users and roles.
- Roles/capabilities.
- Projects and profiles.
- Environments and domains.
- OTM connection configuration.
- Feature flags.
- Module enablement.
- Audit log.
- Technical configuration.
```

Access rules:

```text
- visible only to ADMIN, DBA, MASTER, or users with explicit capability;
- sensitive configuration must be masked;
- critical changes must generate audit;
- feature flags control dev-only and optional surfaces;
- catalog/governance changes need request, decision, and rollback trail.
```

## 3. Current UI Review

Current screen:

```text
/admin
```

Observed browser state:

```text
- Metrics: Projects, Capabilities, Jobs, Audit events.
- Main panel: Platform jobs with create demo job and 10 visible job rows.
- Side panel: setup authoring, setup status, effective capabilities, selected
  job events, feature flags, and audit trail.
- Setup forms for workspace, project, profile, and environment all live in the
  same side panel.
- Feature flag toggling exists for `dev_tools`.
- Job `View` updates selected job events but does not open a route-level job
  detail screen.
```

What works:

```text
- Backend-backed setup, jobs, audit, flags, and capabilities are visible.
- Job list density is capped.
- Feature flag toggle is backend-backed.
- Setup forms execute real platform actions.
```

Current UX problems:

```text
- Too many unrelated admin responsibilities are stacked on one page.
- Setup authoring is squeezed into a side panel.
- Job administration dominates the Admin Console first screen.
- Job `View` does not visibly change route or story; it updates a side panel.
- Audit is read-only and buried.
- Users/roles/capabilities are represented only as effective context, not as an
  administration journey.
- OTM connection governance is missing from the visible UI.
- There is no route-level edit/copy/delete/retire pattern for project/profile/
  environment/flag/admin objects.
```

## 4. Design Decision

Admin Console should become a **Platform Administration Hub** with separate
route-level areas.

Do not keep adding panels to `/admin`. The first screen should be a command
center that points to clear admin journeys.

Recommended map:

```text
/admin
  Admin hub

/admin/setup
  Workspace/project/profile/environment setup

/admin/users
  Users list and access administration

/admin/users/:userId
  User detail, roles, capabilities, audit

/admin/roles
  Role and capability matrix

/admin/feature-flags
  Feature flag list

/admin/feature-flags/:flagId
  Feature flag detail, edit, history

/admin/jobs
  Platform jobs list

/admin/jobs/:jobId
  Job detail, events, artifacts, safe input/result metadata

/admin/audit
  Audit search

/admin/otm-connections
  OTM connection setup and readiness

/admin/modules
  Module enablement and navigation/capability diagnostics
```

## 5. Route Specifications

### `/admin`

Purpose:

```text
Administration overview and next setup/governance actions.
```

Loads:

```text
GET /api/v1/platform/admin/summary
```

Shows:

```text
- setup readiness;
- pending administrative blockers;
- recent critical audit events;
- failed/running job summary;
- feature flags needing attention;
- OTM connection readiness;
- module governance status.
```

Clicks:

```text
- Setup card opens `/admin/setup`.
- Users card opens `/admin/users`.
- Feature flags card opens `/admin/feature-flags`.
- Jobs card opens `/admin/jobs`.
- Audit card opens `/admin/audit`.
- OTM connections card opens `/admin/otm-connections`.
```

Must not show:

```text
- full setup forms;
- full job event detail;
- all audit rows;
- raw credentials;
- business module actions.
```

### `/admin/setup`

Purpose:

```text
Create and maintain workspace, project, profile, environment, and domain setup.
```

Loads:

```text
GET /api/v1/platform/workspaces
GET /api/v1/platform/projects
GET /api/v1/platform/profiles
GET /api/v1/platform/environments
GET /api/v1/platform/projects/{project_id}/setup-status
```

Clicks:

```text
- Create workspace opens `/admin/setup/workspaces/new`.
- Workspace row opens `/admin/setup/workspaces/:workspaceId`.
- Project row opens `/admin/setup/projects/:projectId`.
- Profile row opens `/admin/setup/profiles/:profileId`.
- Environment row opens `/admin/setup/environments/:environmentId`.
- Back returns to `/admin`.
```

Actions:

```text
- create workspace;
- create project;
- create profile;
- create environment;
- edit supported metadata;
- retire/delete only when backend exposes guarded action;
- audit every critical setup mutation.
```

### `/admin/users`

Purpose:

```text
Manage users, roles, capabilities, and effective access.
```

Loads:

```text
GET /api/v1/platform/admin/users?filters...
GET /api/v1/platform/admin/roles
GET /api/v1/platform/admin/capabilities
```

Required filters:

```text
- email: begins with, contains, one of, not one of;
- role: one of, not one of;
- capability: contains, one of, not one of;
- status;
- project/profile access.
```

Clicks:

```text
- User row opens `/admin/users/:userId`.
- Role chip opens role/capability explanation.
- Back returns to `/admin`.
```

Actions:

```text
- invite/create synthetic local user if enabled;
- assign role/capability;
- remove role/capability;
- disable user;
- reset local credential only if supported and audited.
```

### `/admin/feature-flags`

Purpose:

```text
Govern optional, experimental, and technical surfaces.
```

Loads:

```text
GET /api/v1/platform/feature-flags?filters...
```

Clicks:

```text
- Flag row opens `/admin/feature-flags/:flagId`.
- Create flag opens `/admin/feature-flags/new`.
```

Actions:

```text
- enable/disable flag;
- change scope;
- explain affected modules/actions;
- audit every change;
- require confirmation for dev-only or production-relevant flags.
```

### `/admin/jobs`

Purpose:

```text
Administer platform jobs without dominating the whole Admin Console.
```

Loads:

```text
GET /api/v1/platform/jobs?filters...
```

Clicks:

```text
- Job row opens `/admin/jobs/:jobId`.
- Module link opens source module object if backend provides safe link.
```

Actions:

```text
- run pending job;
- cancel pending/running job if backend allows;
- create demo job only in local/dev QA context;
- view event timeline;
- view safe artifact/evidence links.
```

### `/admin/jobs/:jobId`

Purpose:

```text
Inspect one job lifecycle clearly.
```

Shows:

```text
- status, progress, source module, type;
- project/profile/environment/domain;
- event timeline;
- safe input/result metadata, never raw sensitive payload by default;
- related artifacts/evidence;
- available actions and disabled reasons.
```

### `/admin/audit`

Purpose:

```text
Search critical platform changes and sensitive operations.
```

Loads:

```text
GET /api/v1/platform/audit?filters...
```

Filters:

```text
- action: begins with, contains, one of, not one of;
- target type;
- target id: begins with, contains, one of, not one of;
- user;
- date range;
- sensitivity.
```

### `/admin/otm-connections`

Purpose:

```text
Configure and validate OTM connection readiness without exposing secrets.
```

Rules:

```text
- no raw secret display;
- readiness check returns masked and client-safe status;
- direct OTM submit remains blocked unless this area is ready and capability
  permits it;
- every change is audited.
```

## 6. Global Click Rules

```text
- List row opens a detail route, not a side panel, for admin objects.
- Create opens a route-level form with Back.
- Edit opens a route-level form with Back.
- Delete/retire opens a guarded confirmation route/modal with backend reason.
- Job View opens `/admin/jobs/:jobId`.
- Audit row opens audit detail only if backend exposes client-safe details.
- Disabled action shows backend-provided required capability/flag/setup reason.
```

## 7. Backend Contract Rules

The frontend must not decide:

```text
- who is admin;
- who can see Admin Console;
- whether a flag can be toggled;
- whether a job can run/cancel;
- whether setup is complete;
- whether an OTM connection is ready;
- whether an audit row is sensitive.
```

Backend responses should include:

```text
- available_actions;
- disabled_reason;
- required_capability;
- required_feature_flag;
- audit_required;
- sensitivity_level;
- safe_links;
- masked fields only for secrets.
```

## 8. QA Journeys

Functional QA must cover:

```text
1. USER cannot see Admin Console.
2. ADMIN/DBA/MASTER can open `/admin`.
3. Setup card opens `/admin/setup` and Back returns to `/admin`.
4. Create workspace/project/profile/environment validates missing fields.
5. Feature flag enable/disable requires backend permission and records audit.
6. Job list filters and job row opens `/admin/jobs/:jobId`.
7. Run/cancel job handles allowed, disallowed, stale, and already-final states.
8. Audit search handles no results, filters, and sensitive/masked detail.
9. OTM connection route masks secrets and blocks readiness when incomplete.
10. Leaving and returning to each route restores URL-owned filters, not hidden
    local state.
11. Sign out removes authenticated navigation, or the login screen clearly uses
    an unauthenticated shell.
```

## 9. Acceptance Criteria

Admin Console can be considered accepted when:

```text
- it is restricted by backend-owned access;
- it is a hub plus focused admin routes, not one stacked technical page;
- users/roles/capabilities have a real administration journey;
- setup entities have create/detail/edit/retire routes where supported;
- feature flags have history and impact explanation;
- jobs have list/detail/event routes;
- audit has searchable route-level UX;
- OTM connection readiness is represented without exposing secrets;
- every critical mutation is audited;
- no normal business-module workflow depends on visiting Admin Console unless
  setup or permission is missing.
```
