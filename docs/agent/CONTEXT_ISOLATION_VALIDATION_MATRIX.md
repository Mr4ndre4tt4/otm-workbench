# Context Isolation Validation Matrix

**Status:** active foundation baseline
**Date:** 2026-05-28
**GitHub issue:** #214

## Purpose

This matrix defines the validation gate for client/domain, environment, Public
View, access-policy visibility, and DBA visibility before the next module
delivery lane continues.

The project invariant is:

```text
Every operational record carries explicit client/domain, environment, and
visibility/access-policy scope. Public View is a separate shared scope. DBA can
see across scopes; normal users operate only inside allowed scopes.
```

## Current Backend Foundation

| Area | Current evidence | Status |
|---|---|---|
| Active context defaults | `GET /api/v1/platform/active-context` returns Public-only domain visibility when no context is selected. | Covered |
| Active context selection | Active project/profile/environment/domain can be selected and read back with allowed domains. | Covered |
| Project/profile/environment selectors | Non-admin setup selectors are limited to granted projects. | Covered |
| Grant and policy authoring | Settings access model, grant creation, and policy creation are authority checked. | Covered |
| Public View semantics | Public domain is listed separately from private domain access. | Covered at platform contract level |
| DBA visibility | Admin/DBA style users retain broad setup visibility. | Covered by admin paths; module-level checks vary |
| Runtime navigation freshness | `tests/test_modules_navigation.py` guards current UI phase navigation. | Covered |

## Module Matrix

| Module | Primary scoped records | Existing isolation evidence | Gap / next validation |
|---|---|---|---|
| Settings | projects, profiles, environments, users, roles, grants, access policies | `tests/test_operational_context.py` covers setup visibility, active context, grants, policies, and recovery. | Keep as source of truth for context foundation. |
| Cockpit | active context, project info, accelerator availability | Platform active-context and navigation tests cover backend prerequisites. | Needs browser route recovery and context selector evidence before Cockpit completion. |
| Rates Studio | rate batches, tables, rows, issues, generated artifacts | Rates routes resolve create scope from active context and module tests include scoped batch behavior. | Revalidate in the next Rates lane with same-name batches across domains/environments. |
| Load Plan / Cutover | packages, checklists, readiness, review items, handoff/export records | Load Plan package and checklist tests include scoped package behavior and hidden-context rejection. | Preserve as dependency; add any missing Public View copy/use cases later. |
| Assets Library | assets, versions, links, classifications | Assets tests now cover active-context inheritance, BATCH/CHECKLIST scoped links, archive/detail contracts, and target version taxonomy. | Add browser evidence only when visual acceptance is in scope. |
| Master Data / Data Factory | batches, templates, validation artifacts, coordinate quality records | Existing module tests cover functional behavior; context-isolation coverage must be revalidated before the Master Data lane resumes. | Create a focused issue before Master Data continuation. |
| Order Release Generator | templates, batches, rows, XML artifacts | Existing revalidation exists; scope inheritance is implemented in backend helpers. | Revalidate direct route recovery and cross-domain template visibility before completion. |
| Integration Mapping Studio | systems, mappings, preview/spec/artifacts | Reserved for separate chat/workstream. | Do not modify here unless a minimal cross-module context fix is required. |

## Validation Commands

Use these as the minimum foundation gate before browser QA or module acceptance:

```powershell
python -m pytest tests/test_operational_context.py -q
python -m pytest tests/test_modules_navigation.py -q
```

For module continuation, add the module-specific isolation suite or create one
before claiming completion.

## Follow-Up Issues To Open

Open small issues only when the next lane starts:

- Cockpit: context selector browser route recovery and Public/private visual
  evidence.
- Rates: same-name batch isolation across domain/environment before Rates
  completion.
- Master Data: focused context-isolation revalidation before continuation.
- Order Release: scoped template/batch route recovery before completion.

Do not create broad placeholder issues for every module at once; attach them to
the active version lane when implementation starts.

## Acceptance Gate

A future module slice can claim context-safe completion only when it records:

- active context used;
- private domain/environment used;
- Public View behavior when applicable;
- normal-user allowed and denied behavior;
- DBA/admin visibility behavior where applicable;
- generated artifact/evidence scope;
- browser QA runtime navigation freshness when screenshots are captured.
