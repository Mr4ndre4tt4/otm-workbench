# GUI General Screen Pass

**Status:** active QA/product review  
**Date:** 2026-05-26  
**Scope:** browser-backed pass from login through the current module routes,
focused on hidden placeholder screens, unclear clicks, missing module specs,
and documentation gaps.

## 1. Environment

```text
Backend: http://127.0.0.1:8000
Frontend: http://127.0.0.1:5173
User: demo@example.test
Data: synthetic QA/dev data only
```

Commands used to bring the app up locally:

```powershell
python -m uvicorn otm_workbench.main:app --host 127.0.0.1 --port 8000
python -m otm_workbench.cli bootstrap-qa-user
npm run dev -- --host 127.0.0.1 --port 5173
```

## 2. Pass Summary

The general shell, login, theme controls, density control, sidebar collapse, and
module navigation are operational. The product still needs stronger route-level
storytelling in several modules, but most of those gaps are already covered by
module-specific consolidated specs.

New documentation gaps found in this pass:

```text
1. Admin Console needed its own consolidated route-level spec.
2. Developer Tools needed its own consolidated route-level spec.
3. A general shell/auth follow-up is needed for post-sign-out navigation.
4. Global cockpit actions need clear routes or visible outcomes.
5. OTM Catalog Core remains the main module with only a view contract, not a
   consolidated redesign spec.
```

## 3. Route Results

| Route | Result | Finding |
|---|---|---|
| `/` then login | Passed | Login works with backend-owned session. |
| `/home` | Passed with UX gaps | Project Cockpit loads and shell controls work. `View jobs` and `View evidence` buttons click but do not visibly change route/state. |
| `/master-data` | Passed, already known UX gap | Dense staged workflow remains on one route; covered by `GUI_MASTER_DATA_DATA_FACTORY_REDESIGN_SPEC.md`. |
| `/evidence` | Passed, already known UX gap | Filter/list/detail/archive surfaces work but remain dense; covered by `GUI_EVIDENCE_HUB_CONSOLIDATED_SPEC.md`. |
| `/rates` | Passed, already known UX gap | Batch list/detail/actions work but remain dense; covered by `GUI_RATES_STUDIO_CONSOLIDATED_SPEC.md`. |
| `/catalog` | Passed, needs deeper spec | Catalog validation, schema guidance, macro objects, and selected object are all on one page; only `GUI_CATALOG_CORE_VIEW.md` exists. |
| `/load-plan` | Passed, already known UX gap | Many staged actions on one route; covered by `GUI_LOAD_PLAN_CUTOVER_CONSOLIDATED_SPEC.md`. |
| `/assets` | Passed, already known UX gap | Library/create/version/link/lifecycle surfaces are one-route dense; covered by `GUI_ASSETS_LIBRARY_CONSOLIDATED_SPEC.md`. |
| `/order-release-generator` | Passed, already known UX gap | Template/batch/preview/artifact/submit are route-dense; covered by `GUI_ORDER_RELEASE_GENERATOR_CONSOLIDATED_SPEC.md`. |
| `/integration-mapping` | Passed, already known UX gap | Systems/definition/payload/rules/list are one-route dense; covered by `GUI_INTEGRATION_MAPPING_CONSOLIDATED_SPEC.md`. |
| `/admin` | Passed, spec gap closed in this pass | Current UI works but mixes jobs, setup, flags, audit, capabilities in one page; now covered by `GUI_ADMIN_CONSOLE_CONSOLIDATED_SPEC.md`. |
| `/dev-tools` | Placeholder found | Developer Tools is still the shared placeholder route; now covered by `GUI_DEVELOPER_TOOLS_CONSOLIDATED_SPEC.md`. |
| unknown route | Passed with UX gap | Shows `Module unavailable`, but there is no obvious `Back to home` action. |

## 4. Click Findings

Safe clicks performed:

```text
- sidebar collapse and expand;
- light mode;
- dark mode;
- compact density;
- Project Cockpit View jobs;
- Project Cockpit View evidence;
- staged navigation in Master Data;
- Evidence filters apply/reset;
- Rates Validate;
- Catalog Validate table and Reset catalog validation;
- Load Plan stage navigation;
- Assets stage navigation and filter apply;
- Order Release stage navigation;
- Integration Mapping stage navigation;
- Admin job View;
- Developer Tools placeholder content;
- Sign out.
```

Results:

```text
- Shell controls worked.
- Stage buttons generally changed visible content but stayed on the same route.
- Filter/validation buttons executed without browser failure.
- Admin job `View` did not visibly change route; it updates a side panel.
- Project Cockpit `View jobs` and `View evidence` clicked successfully but did
  not visibly navigate or change the screen.
- Developer Tools has no real actions besides shell controls.
- Sign out returned to the login form, but kept the sidebar navigation visible
  and kept the URL at `/home`.
```

## 5. New Issues To Track

### Shell/Auth

Linear: `OTM-172`

Post-sign-out state should not show authenticated navigation as if the user
were still inside the app.

Expected:

```text
- either route to `/login` with unauthenticated shell only;
- or keep `/home` but hide module navigation and authenticated actions.
```

Why it matters:

```text
The current UI shows the full sidebar beside the login form after sign out.
This creates confusing state and may expose navigation labels that should be
backend-owned and session-scoped.
```

### Project Cockpit Global Actions

Linear: `OTM-173`

`View jobs` and `View evidence` need visible outcomes.

Expected:

```text
- `View jobs` opens `/home/jobs` or `/admin/jobs` depending on role and
  backend action contract;
- `View evidence` opens `/evidence` with project/context filter or a cockpit
  evidence route;
- disabled/missing targets show backend reason.
```

### Unknown Route Recovery

`Module unavailable` should give a clear recovery action.

Expected:

```text
- Back to Project Cockpit;
- Back to previous route;
- explain whether the route is missing, blocked by capability, or blocked by
  feature flag.
```

### Catalog Core Consolidated Spec

Linear: `OTM-174`

Catalog Core still needs the same consolidated redesign exercise as the other
modules.

Reason:

```text
It has a working view contract, but it is now a central dependency for Rates,
Master Data, Integration Mapping, Order Release, Assets, Developer Tools, and
schema-pack analysis. Its UI should be a route-level Catalog Hub, not one page
mixing schema guidance, validation, macro object list, and selected object.
```

### Long Row Accessible Names

Linear: `OTM-175`

Several row buttons expose the entire row text as the button name.

Examples:

```text
- Evidence rows include type/module/artifact/status as one large button label.
- Rates rows include batch name/scenario/table counts/status.
- Assets and Order Release rows show long synthetic identifiers.
```

Expected:

```text
- row button accessible name should be concise, such as `Open evidence ...`;
- row metadata should remain visible text, not merged into an oversized button
  name;
- long IDs should be truncated visually but copyable in detail routes.
```

### Developer Tools Placeholder

Linear: `OTM-176`

Developer Tools is visible when `dev_tools` is enabled, but the route still uses
the generic placeholder screen. It should either be hidden until contracts exist
or replaced by the governed technical hub described in
`GUI_DEVELOPER_TOOLS_CONSOLIDATED_SPEC.md`.

### Admin Console Route-Level Redesign

Linear: `OTM-177`

Admin Console is functional, but jobs, setup forms, feature flags,
capabilities, selected job events, and audit all compete on one page. It should
move to the route-level administration hub described in
`GUI_ADMIN_CONSOLE_CONSOLIDATED_SPEC.md`.

## 6. Documentation Updates Made In This Pass

```text
- Created GUI_ADMIN_CONSOLE_CONSOLIDATED_SPEC.md.
- Created GUI_DEVELOPER_TOOLS_CONSOLIDATED_SPEC.md.
- Created GUI_GENERAL_SCREEN_PASS_2026_05_26.md.
- Updated GUI_MODULE_ROADMAP_INDEX.md.
- Updated GUI_CONTRACT_INDEX.md.
- Updated GUI_MODULE_EXPERIENCE_ROADMAP.md.
```

## 7. Recommended Next Documentation

```text
1. GUI_CATALOG_CORE_CONSOLIDATED_SPEC.md
   Highest remaining module-specific documentation gap.

2. GUI_SHELL_AUTH_SIGNOUT_RECOVERY_SPEC.md
   Small but important shell/auth clarity issue.

3. GUI_GLOBAL_ACTION_DESTINATION_CONTRACT.md
   Define how page-header/global actions route to jobs, evidence, settings,
   artifacts, and module-specific destinations.

4. GUI_ROW_ACCESSIBLE_NAME_CONTRACT.md
   Prevent entire rows from becoming huge button labels.
```

## 8. Recommended Implementation Order

```text
1. Fix sign-out shell state.
2. Give Project Cockpit `View jobs` and `View evidence` real route outcomes.
3. Replace Developer Tools placeholder with a gated technical hub or hide it
   until the hub contract exists.
4. Create Catalog Core consolidated route-level spec.
5. Apply row accessible-name cleanup across object lists.
6. Continue module-by-module route-level redesign implementation.
```
