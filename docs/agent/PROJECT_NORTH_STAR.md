# Project North Star

**Status:** active
**Date:** 2026-05-26

## North Star

OTM Workbench should feel like a local-first accelerator workbench for Oracle
Transportation Management projects. A consultant should always know:

- where they are;
- which client/domain and environment context is active;
- whether they are working in private client data or Public View;
- which accelerator can help with the task at hand;
- what object they are working on inside the selected accelerator;
- what evidence or artifact exists for that accelerator.

## Product Principles

1. Backend-owned truth before frontend polish.
2. Data isolation by client/domain, environment, and visibility policy is a
   product invariant.
3. Modules are accelerators that can be used in any project phase, not a forced
   project workflow.
4. Every module needs a clear primary object and lifecycle.
5. Complex actions deserve route-level screens or deliberate modals.
6. Evidence is client-safe and traceable.
7. OTM technical uncertainty must be validated through the Data Dictionary and
   official Oracle documentation.
8. UI redesign starts from validated module scope and wireframes, not from
   patching the current implementation.
9. Cleanup is reversible until explicitly approved.
10. Every module delivery starts by revalidating the desired user outcome,
    required To-Be screens, valid synthetic fixtures, and OTM dependency
    evidence.

## What Good Looks Like

A module is complete only when:

- backend/API contracts exist and are tested;
- UI is clear and not overloaded;
- every click has an obvious destination;
- actions execute expected backend behavior;
- browser QA covers happy, negative, out-of-order, and route recovery paths;
- evidence and screenshots exist for meaningful states;
- docs, Linear, GitHub, tests, and QA evidence agree.

## What To Avoid

- treating a first functional slice as module completion;
- adding all backend panels to one page;
- using placeholders as public modules;
- exposing dev/DBA tools to normal users;
- making the Cockpit a project-management or readiness-control dashboard;
- forcing users through a project phase/order before using an accelerator;
- mixing private client/domain data into Public View;
- letting stale docs remain active without classification;
- deleting files before archive approval;
- using real client data.
