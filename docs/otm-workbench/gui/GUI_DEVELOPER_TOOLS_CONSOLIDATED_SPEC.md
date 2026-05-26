# GUI Developer Tools Consolidated Specification

**Status:** active redesign specification  
**Date:** 2026-05-26  
**Scope:** consolidated Developer / DBA Tools objective, current UI review,
route-level redesign, backend contract rules, and QA acceptance criteria.

## 1. Objective

Developer Tools exists to expose technical diagnostics and DBA/developer
utilities only to authorized technical users.

The original goal is not to create another business module. It is to provide a
controlled technical surface for troubleshooting, schema inspection, environment
comparison, optional Oracle Lab workflows, and internal diagnostics without
polluting the normal consultant journey.

Developer Tools must answer:

```text
- What technical diagnostics are available for this user and context?
- Which feature flag and capability enabled each tool?
- Which OTM/catalog/schema/debug resource can be inspected safely?
- Which environment readiness or comparison issue needs technical attention?
- What diagnostic action was executed, by whom, and with what client-safe
  result?
```

## 2. Original Functional Scope

Source foundation docs describe Developer / DBA Tools as controlled technical
tools:

```text
- OTM Explorer: dev/DBA-only or archived.
- Data Dictionary Explorer: technical/Admin/DBA support.
- FK Catalog Explorer: technical validation/reference support.
- Environment Compare: redesign as Environment Readiness or retire.
- Oracle Lab / SQL Lab: optional, technical, not public.
- Setup Assets: absorb into Load Plan / Cutover.
```

Access rules:

```text
- Hidden from the public menu.
- Requires specific capability.
- Requires the relevant feature flag.
- Must not become a dependency for normal USER execution.
- Useful functionality should graduate into main module flows when it becomes
  product-facing.
```

Technical foundation rules add:

```text
role DBA/MASTER
+ specific capability
+ feature flag enabled
```

## 3. Current UI Review

Current state:

```text
- The route is registered by backend navigation as `dev_tools`.
- The frontend has no dedicated Developer Tools view.
- `dev_tools` uses the generic module placeholder in `WorkbenchRoute`.
- The sidebar label and icon exist.
- The description says it is for internal diagnostics behind admin and feature
  flag controls.
- Feature flag toggling for `dev_tools` is currently handled in Admin Console.
```

Browser review:

```text
- Direct browser navigation to `/dev-tools` failed with a blocked-client route
  response in the current in-app browser session.
- Navigating from the app could not be completed in that session after the
  blocked direct route.
- Code review confirms there is no dedicated Developer Tools screen; available
  users see the shared placeholder.
```

Current solution quality:

```text
- Good: route/label/icon/feature flag concept exists.
- Good: it is already treated as restricted and non-public.
- Weak: the screen does not explain what problem it solves.
- Weak: there are no tool cards, no diagnostics routes, no audit-oriented
  workflow, and no clear permission/flag reason.
- Weak: it risks becoming a junk drawer if tools are added to one page without
  a route-level story.
- Weak: no evidence yet that it accelerates troubleshooting.
```

## 4. Design Decision

Developer Tools should become a **Technical Diagnostics Hub**.

It should not use the normal module authoring workflow, and it should not be a
single page with every debug panel stacked together. It needs a controlled hub
with separate route-level tools.

Recommended pattern:

```text
/dev-tools
  Technical tools hub

/dev-tools/data-dictionary
  Data Dictionary Explorer

/dev-tools/fk-catalog
  FK Catalog Explorer

/dev-tools/schema-packs
  WSDL/XSD/schema pack diagnostics

/dev-tools/environment-readiness
  Environment readiness and comparison diagnostics

/dev-tools/otm-explorer
  Guarded OTM Explorer, only if approved

/dev-tools/oracle-lab
  Optional Oracle Lab / SQL Lab, disabled by default

/dev-tools/diagnostic-runs/:runId
  Diagnostic run result and audit-safe output
```

The hub must show only tools returned by the backend as available for the
current user, active context, feature flags, and capabilities.

## 5. Non-Goals

Developer Tools must not:

```text
- appear for normal USER profiles;
- become required for Rates, Master Data, Load Plan, Assets, Evidence, Order
  Release, or Integration Mapping success;
- expose raw OTM credentials, secrets, database passwords, or raw sensitive
  payloads;
- become a general SQL console available by default;
- duplicate Catalog Core as a functional catalog UI;
- duplicate Admin Console setup/permission management;
- duplicate Load Plan setup asset workflows;
- store durable settings only in frontend state;
- infer permission, masking, or feature-flag state in the frontend.
```

## 6. Core Navigation Map

```text
/dev-tools
  Purpose:
    Technical entry point for authorized DBA/MASTER users.

  Loads:
    GET /api/v1/platform/dev-tools/summary

  Shows:
    - available technical tools
    - disabled tools with backend reason
    - active project/profile/environment/domain context
    - recent diagnostic runs
    - recent audit events for dev tools

  Primary action:
    Open selected diagnostic tool.

  Must not show:
    - raw debug JSON as the first screen
    - SQL input
    - all tool panels stacked vertically
```

```text
/dev-tools/data-dictionary
  Purpose:
    Explore OTM table/column metadata and official documentation hints for
    technical debugging.

  Loads:
    GET /api/v1/platform/dev-tools/data-dictionary?filters...

  Clicks:
    - Search opens filtered result list in same route.
    - Table row opens `/dev-tools/data-dictionary/tables/:tableName`.
    - Column row opens column detail as a route or drawer only if small.
    - Back returns to `/dev-tools`.

  Actions:
    - Validate table reference.
    - Validate column reference.
    - Copy client-safe reference path.
    - Send useful reference back to Catalog Core, if backend exposes action.
```

```text
/dev-tools/fk-catalog
  Purpose:
    Inspect dependencies and foreign-key style relationships used by validation
    and load ordering.

  Loads:
    GET /api/v1/platform/dev-tools/fk-catalog?source_table=...

  Clicks:
    - Dependency row opens relationship detail.
    - Related table opens Data Dictionary table detail.
    - Back returns to `/dev-tools`.

  Actions:
    - Build dependency trace.
    - Export client-safe dependency summary.
```

```text
/dev-tools/schema-packs
  Purpose:
    Inspect WSDL/XSD/schema-pack roots and operations used by Integration
    Mapping and Order Release Generator.

  Loads:
    GET /api/v1/platform/dev-tools/schema-packs
    GET /api/v1/platform/dev-tools/schema-packs/:id/roots

  Clicks:
    - Schema pack row opens pack detail.
    - Root row opens root path browser.
    - Operation row opens operation/message detail.

  Actions:
    - Validate root availability.
    - Copy schema path reference.
    - Create insight candidate for Catalog/Core roadmap, if supported.
```

```text
/dev-tools/environment-readiness
  Purpose:
    Diagnose environment setup and compare safe metadata across environments.

  Loads:
    GET /api/v1/platform/dev-tools/environment-readiness

  Clicks:
    - Environment row opens readiness detail.
    - Difference row opens field-level explanation.

  Actions:
    - Run readiness check.
    - Export readiness summary.
    - Create Admin Console setup task, if backend supports it.
```

```text
/dev-tools/otm-explorer
  Purpose:
    Optional guarded OTM object explorer for DBA/MASTER only.

  Loads:
    GET /api/v1/platform/dev-tools/otm-explorer/readiness

  Required gate:
    role DBA/MASTER
    + capability
    + feature flag
    + configured connection
    + explicit audit intent

  Actions:
    - Run read-only query/search.
    - Mask sensitive fields.
    - Save client-safe diagnostic evidence.

  Default:
    Disabled until governance is approved.
```

```text
/dev-tools/oracle-lab
  Purpose:
    Optional local Oracle compatibility sandbox.

  Loads:
    GET /api/v1/platform/dev-tools/oracle-lab/readiness

  Required gate:
    local service available
    + feature flag
    + capability

  Actions:
    - Run controlled compatibility check.
    - View sanitized result.
    - Create diagnostic run artifact.

  Default:
    Disabled; never required for normal module execution.
```

## 7. Click Rules

Every click must have a clear result:

```text
Hub tool card
  Opens the tool route. Does not expand a hidden panel on the hub.

Disabled tool card
  Opens a permission/setup explanation route or modal with backend-provided
  reason, required capability, required flag, and next admin action.

Recent diagnostic run row
  Opens `/dev-tools/diagnostic-runs/:runId`.

Back
  Always returns to the previous Developer Tools route or hub.

Open in module
  Moves to Catalog Core, Integration Mapping, Order Release, Admin Console, or
  Load Plan only when backend returns an explicit linked action.
```

## 8. Action Rules

Technical actions must be backend-owned:

```text
- Backend defines available actions.
- Backend validates capability and feature flag.
- Backend masks sensitive fields.
- Backend writes audit log for access and critical actions.
- Backend creates diagnostic run records for long-running actions.
- Backend returns client-safe output only.
- Frontend renders disabled reasons; it does not calculate them.
```

Action examples:

```text
Run readiness check
  POST /api/v1/platform/dev-tools/environment-readiness/runs

Inspect schema root
  GET /api/v1/platform/dev-tools/schema-packs/:id/roots/:rootId

Build dependency trace
  POST /api/v1/platform/dev-tools/fk-catalog/traces

Run guarded OTM search
  POST /api/v1/platform/dev-tools/otm-explorer/search

Run Oracle Lab check
  POST /api/v1/platform/dev-tools/oracle-lab/checks
```

## 9. Backend Contract Alignment

Existing foundation:

```text
- navigation exposes `dev_tools`;
- feature flag `dev_tools` can be toggled in Admin Console;
- backend-owned navigation/capabilities already decide module visibility;
- Admin Console exposes jobs, audit, flags, setup, and capabilities.
```

Needed contracts before a real Developer Tools UI:

```text
GET /api/v1/platform/dev-tools/summary
GET /api/v1/platform/dev-tools/tools
GET /api/v1/platform/dev-tools/diagnostic-runs
GET /api/v1/platform/dev-tools/diagnostic-runs/{run_id}
GET /api/v1/platform/dev-tools/data-dictionary
GET /api/v1/platform/dev-tools/fk-catalog
GET /api/v1/platform/dev-tools/schema-packs
GET /api/v1/platform/dev-tools/environment-readiness
GET /api/v1/platform/dev-tools/otm-explorer/readiness
GET /api/v1/platform/dev-tools/oracle-lab/readiness
```

Each response should include:

```text
- required_role
- required_capability
- required_feature_flag
- availability status
- disabled reason
- allowed actions
- sensitivity level
- audit requirement
- active context
```

## 10. UI States

Required states:

```text
- hidden from USER;
- visible but disabled by missing feature flag;
- visible but disabled by missing capability;
- visible but disabled by missing local service;
- visible but disabled by missing OTM connection;
- empty diagnostics;
- no results;
- blocked sensitive output;
- masked output;
- diagnostic running;
- diagnostic succeeded;
- diagnostic failed;
- audit/event unavailable;
- route leave/return with preserved filters.
```

## 11. QA Journeys

Functional QA must cover:

```text
1. USER cannot see Developer Tools in navigation.
2. DBA/MASTER without feature flag sees no route or sees backend disabled
   reason, depending on navigation contract.
3. DBA/MASTER with feature flag opens `/dev-tools`.
4. Hub shows available and disabled tools from backend.
5. Disabled tool explains required flag/capability/service.
6. Data Dictionary search handles exact, begins-with, contains, no results,
   and invalid table.
7. FK trace handles valid dependency, missing source table, and no dependency.
8. Schema pack explorer handles valid root, invalid root, and large path list
   without layout collapse.
9. Environment readiness run creates a diagnostic run and audit event.
10. OTM Explorer remains blocked until governance/readiness is true.
11. Oracle Lab remains optional and blocked when local service is unavailable.
12. Leaving and returning to a tool preserves filters only through
    backend-owned or URL-owned state, not hidden local memory.
13. Sensitive output is masked in UI, audit, evidence, and downloads.
14. Browser console has no errors after route navigation and blocked actions.
```

## 12. Implementation Slices

Recommended order:

```text
Slice 1: Keep placeholder, add blocked-state route contract
  - Ensure `/dev-tools` has explicit unavailable/disabled behavior.
  - Add QA for USER hidden and feature-flag/capability gating.

Slice 2: Developer Tools hub
  - Add `/dev-tools` dedicated screen.
  - Backend summary returns available tools, disabled reasons, and recent runs.

Slice 3: Data Dictionary and FK explorers
  - Add technical read-only explorers backed by Catalog/Data Dictionary.
  - No raw ad hoc SQL.

Slice 4: Schema pack diagnostics
  - Expose WSDL/XSD roots, operations, paths, and schema insights.
  - Link useful findings back to Catalog Core and Integration Mapping roadmap.

Slice 5: Environment readiness
  - Redesign Environment Compare as readiness diagnostics.
  - Export client-safe summary and audit run.

Slice 6: Optional guarded OTM Explorer / Oracle Lab
  - Implement only after security review and explicit governance approval.
```

2026-05-26 Slice 1A delivered:

```text
/dev-tools no longer renders the generic module placeholder.
The route opens a dedicated Technical Diagnostics Hub with a backend-gated
status summary, clear contract-pending state, backend gate checklist, and no
diagnostic tool panels before backend-owned summary contracts exist.
Browser QA enables the backend `dev_tools` feature flag, opens the route,
verifies the guarded state, rejects the old generic placeholder, and captures
output/gui-qa/developer-tools/01-developer-tools-guarded-hub.png.
```

2026-05-26 Slice 2A delivered:

```text
GET /api/v1/platform/dev-tools/summary now returns the backend-owned hub
contract for authorized admin/technical users when the dev_tools feature flag is
enabled.
The contract includes active context, guard reasons, available and disabled
tools, disabled reasons, counts, and recent diagnostic runs without raw input or
result payloads.
/dev-tools consumes that summary and renders a compact hub: metrics, backend
gate rows, available/disabled tool rows, and recent run metadata. It still does
not render real tool panels or SQL/OTM explorer actions before dedicated route
contracts exist.
Browser QA seeds synthetic context and a safe dev_tools DEMO_ECHO run, opens the
route, verifies backend summary rows, rejects the old generic placeholder, and
captures output/gui-qa/developer-tools/01-developer-tools-guarded-hub.png.
```

2026-05-26 Slice 3A delivered:

```text
GET /api/v1/platform/dev-tools/data-dictionary now returns a read-only,
client-safe Data Dictionary table list guarded by admin access and the
dev_tools feature flag.
GET /api/v1/platform/dev-tools/data-dictionary/tables/{table_name} returns
backend-owned table detail plus columns without exposing local file paths.
/dev-tools renders backend-owned tool rows as explicit route links. The Data
Dictionary Explorer opens at /dev-tools/data-dictionary, supports URL-owned
query state such as ?query=rate_geo, shows compact table metadata, and includes
a visible Back to Developer Tools route.
The list view intentionally stays compact: descriptions and deeper column
inspection remain backend-owned detail scope rather than crowding the first
explorer screen.
Browser QA now clicks from the hub into the explorer, verifies filtered
RATE_GEO_COST metadata, checks console/HTTP health, and captures desktop plus
mobile evidence:
output/gui-qa/developer-tools/01-developer-tools-guarded-hub.png
output/gui-qa/developer-tools/02-data-dictionary-explorer.png
output/gui-qa/developer-tools/03-data-dictionary-explorer-mobile.png.
```

2026-05-26 Slice 3B delivered:

```text
/dev-tools/data-dictionary now renders each table row with an explicit Open
table action.
/dev-tools/data-dictionary/tables/{table_name} is now a route-level table
detail UI consuming the existing backend table-detail contract. It shows table
description, column count, foreign-key count, data category, CSVUTIL readiness,
compact column metadata, source contract, backend-owned guardrails, and a
visible Back to Data Dictionary route.
The column list is intentionally capped to the first 40 visible rows with a
showing-count summary so wide Data Dictionary tables do not overload the first
detail screen. Backend still returns the full column contract; richer filtering
or pagination remains a follow-up scope.
Browser QA now opens RATE_GEO_COST from the explorer, verifies loaded column
metadata, checks console/HTTP health, and captures desktop plus mobile evidence:
output/gui-qa/developer-tools/03-data-dictionary-table-detail.png
output/gui-qa/developer-tools/04-data-dictionary-table-detail-mobile.png.
```

2026-05-26 Slice 3C delivered:

```text
GET /api/v1/platform/dev-tools/fk-catalog?source_table=... now returns a
client-safe foreign-key relationship list for a source table, guarded by admin
access and the dev_tools feature flag. Missing source tables return a
Developer Tools-specific not-found error, and the payload exposes no local Data
Dictionary file paths.
/dev-tools/fk-catalog is now a dedicated route-level FK Catalog Explorer. It
defaults to RATE_GEO_COST when no source_table query parameter is supplied,
shows relationship totals, caps the visible list to 12 rows with a showing-count
summary, links each parent table to the Data Dictionary table detail route, and
keeps a visible Back to Developer Tools route.
Browser QA verifies the hub FK Catalog link, direct FK Catalog route recovery,
relationship metadata, parent-table links, console/HTTP health, and captures
desktop plus mobile evidence:
output/gui-qa/developer-tools/05-fk-catalog-explorer.png
output/gui-qa/developer-tools/06-fk-catalog-explorer-mobile.png.
```

2026-05-26 Slice 3D delivered:

```text
GET /api/v1/platform/dev-tools/schema-packs now returns client-safe
schema-pack diagnostics from Catalog Core, guarded by admin access and the
dev_tools feature flag. The route supports otm_version, code, status, and limit
filters so browser QA can isolate a synthetic pack without exposing local source
folders or schema paths.
/dev-tools/schema-packs is now a dedicated route-level Schema Pack Diagnostics
screen. It shows pack/root counts, OTM version, governed schema roots, source
contract, backend-owned guardrails, and a visible Back to Developer Tools route.
The UI intentionally stays read-only and compact; deep path browsing remains in
Catalog Core schema guidance and product-facing authoring remains in Integration
Mapping or Order Release.
Browser QA seeds a synthetic schema pack through Catalog Core APIs, indexes it,
opens the Developer Tools route, verifies the schema root metadata, checks
console/HTTP health, and captures desktop plus mobile evidence:
output/gui-qa/developer-tools/07-schema-pack-diagnostics.png
output/gui-qa/developer-tools/08-schema-pack-diagnostics-mobile.png.
```

2026-05-26 Slice 3E delivered:

```text
GET /api/v1/platform/dev-tools/environment-readiness now returns a
client-safe readiness view for the active implementation context, guarded by
admin access and the dev_tools feature flag. The payload exposes active-context
checks, active environment id, safe environment names/types/statuses, counts,
and the source contract without OTM connection details or credentials.
/dev-tools/environment-readiness is now a dedicated route-level Environment
Readiness screen. It shows environment, ready-check, and blocked-check metrics,
readiness checks, active environment scope, domain scope, source contract, and
a visible Back to Developer Tools route.
Browser QA opens the route from the seeded active context, verifies active
environment/domain readiness, checks console/HTTP health, and captures desktop
plus mobile evidence:
output/gui-qa/developer-tools/09-environment-readiness.png
output/gui-qa/developer-tools/10-environment-readiness-mobile.png.
```

## 13. Acceptance Criteria

Developer Tools can be considered accepted when:

```text
- normal USER cannot see it;
- DBA/MASTER access requires backend capability and feature flag;
- hub has a clear purpose and one primary action per tool card;
- each real tool has its own route and Back action;
- no tool panels are stacked into one disconnected page;
- no sensitive payload, credential, or real client data is exposed;
- all diagnostic actions create audit or diagnostic run history;
- useful technical findings can link back to the relevant main module instead
  of trapping the user in Dev Tools;
- functional UI tests cover happy path, negative path, permission path,
  blocked path, and route leave/return recovery;
- Developer Tools remains optional for normal project delivery.
```
