# Workbench Assistant Diagram Plan

## Purpose

This document lists the diagrams that should be created before implementation.
The first version exists as Mermaid diagrams in planning docs. After review, the
same inventory can be converted into Figma or FigJam boards.

## Diagram Inventory

| ID | Diagram | Current location | Future visual artifact |
|---|---|---|---|
| D01 | High-level assistant architecture | `TARGET_ARCHITECTURE.md` | FigJam architecture board |
| D02 | Local/online operating modes | `TARGET_ARCHITECTURE.md` | FigJam state board |
| D03 | User entry flow | `FLOWS.md` | Figma flow board |
| D04 | Workbench help sequence | `FLOWS.md` | FigJam sequence board |
| D05 | Finder macroflow | `FLOWS.md` | FigJam flow board |
| D06 | Navigation macroflow | `FLOWS.md` | FigJam flow board |
| D07 | SQL helper flow | `SQL_HELPER_DESIGN.md` | FigJam technical flow |
| D08 | SQL explain-query flow | `SQL_HELPER_DESIGN.md` | FigJam technical flow |
| D09 | Oracle docs lookup sequence | `FLOWS.md` | FigJam sequence board |
| D10 | Permission denied flow | `FLOWS.md` and `SOURCE_INDEX_DESIGN.md` | security flow board |
| D11 | UI state map | `UI_EXPERIENCE_SPEC.md` | Figma UI states board |
| D12 | Source indexing pipeline | `SOURCE_INDEX_DESIGN.md` | FigJam data pipeline board |
| D13 | Source index entity concept | `TARGET_ARCHITECTURE.md` | ER/data board |
| D14 | Assistant response contract | `FLOWS.md` | contract board |

## Recommended FigJam Board Sections

```text
01 Product intent and non-goals
02 Architecture overview
03 Local-first knowledge engine
04 Source and permission guard
05 SQL helper
06 Oracle docs lookup and cache
07 UI launcher and panel states
08 Implementation dependency decisions
09 Open questions
```

## Recommended Figma Wireframe Boards

Follow the wireframe calibration workflow before creating these.

```text
01 Launcher closed on Workbench screen
02 Assistant default open panel
03 Help answer state
04 Finder result state
05 SQL draft state
06 Oracle docs result state
07 Permission blocked state
08 Offline limited state
09 Ambiguous clarification state
10 Narrow viewport state
```

## Visual Artifact Gate

Before creating Figma/FigJam artifacts, confirm:

1. desired fidelity: diagram-only, annotated wireframe, or mockup-ready;
2. export target: Figma, FigJam, local HTML, or PNG;
3. board breadth: full product canvas or selected core states;
4. whether the truck-driver robot icon should be conceptual only or visually
   designed in the artifact;
5. whether SQL helper depth should be shown in the UI board or only in a
   technical diagram.

## Current Recommendation

Create FigJam-style technical diagrams first, then Figma wireframes second.

Reason:

- the architecture and permission model are more important than visual polish;
- SQL helper and source indexing need conceptual alignment before UI design;
- the floating launcher/panel can be designed once the backend response
  contract and state inventory are stable.
